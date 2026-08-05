# Guia de execução

Passo a passo para subir o projeto do zero. Todos os comandos são **PowerShell no Windows**.

**Pré-requisitos:** Python 3.13 · Docker Desktop rodando · Git

Tempo total: cerca de 10 minutos, quase todo na ingestão dos 166 mil registros.

---

## Passo 1 — Ambiente virtual

A partir da **raiz do projeto** (`ava_pratica_fiesc/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Se o PowerShell bloquear o script de ativação:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

Com a venv ativa o prompt mostra `(.venv)`. Confira:

```powershell
python --version        # Python 3.13.x
```

---

## Passo 2 — Dependências

```powershell
pip install -r backend\requirements.txt
```

Baixa cerca de 400 MB. Inclui o motor de OCR e o de embeddings, ambos em ONNX —
rodam na CPU, sem GPU e sem chamada de rede.

---

## Passo 3 — Configuração

```powershell
cd backend
Copy-Item .env.example .env
```

Gere os segredos de autenticação:

```powershell
python manage.py secrets
```

Copie a saída para dentro de `backend\.env`, substituindo as linhas correspondentes:

```
JWT_SECRET=...
API_CLIENT_ID=...
API_CLIENT_SECRET=...
INTERNAL_API_KEY=...
```

Preencha também a chave do modelo de linguagem:

```
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-...
```

> Para usar OpenAI: `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4.1-mini` e
> `LLM_BASE_URL=` (vazio).
>
> **A API não sobe sem os segredos** — é proposital. Uma API industrial no ar sem
> autenticação é pior que uma fora do ar: o problema só aparece depois.

---

## Passo 4 — Banco PostgreSQL com pgvector

Ainda dentro de `backend/`:

```powershell
docker network create prescritiva-net
docker compose up -d db
```

Espere ficar `healthy` (uns 10 segundos):

```powershell
docker compose ps
```

> **A imagem é `pgvector/pgvector:pg17`** — PostgreSQL 17 com a extensão já
> compilada. Uma imagem `postgres:17` comum **não serve**: `CREATE EXTENSION vector`
> falha porque a extensão não está instalada.
>
> A porta exposta no host é a **5433**, não a 5432, para não colidir com um
> PostgreSQL já instalado na máquina.

---

## Passo 5 — Criar o schema

```powershell
python manage.py initdb
```

Cria a extensão `vector`, as 5 tabelas e os índices HNSW. É idempotente — rodar de
novo não quebra nada.

Saída esperada:

```
pgvector       0.8.6
vetor sensor   16 dimensoes
vetor doc      384 dimensoes (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
tabelas        document_chunks, documents, fault_document_coverage, index_metadata, sensor_events
```

---

## Passo 6 — Carregar os dados de sensor

```powershell
python manage.py ingest
```

Cerca de 3 minutos. Lê `dados/banner.csv`, normaliza os 151 rótulos em 14 famílias,
calcula o vetor de 16 dimensões e grava com o índice vetorial.

Saída esperada:

```
linhas         166.796
taxonomia      151 rotulos brutos -> 14 familias
total          166.796
  holdout    9.061  10/06/2026 a 16/06/2026
  train    157.735  30/04/2026 a 09/06/2026
```

---

## Passo 7 — Indexar os documentos

```powershell
python manage.py ingest-docs
```

Na primeira execução baixa o modelo de embeddings (220 MB) e roda o OCR do
`Doc1.pdf` — as 17 páginas dele são imagem, sem camada de texto. Uns 2 minutos.

Saída esperada:

```
  Doc1.pdf   ocr  paginas=17 trechos= 26 conf=0.881  -> rolamento
  Doc2.pdf   text paginas= 6 trechos= 16  -> desalinhamento
  Doc3.pdf   text paginas=10 trechos= 18  -> desbalanceamento
  Doc4.pdf   text paginas= 9 trechos= 21  -> correia
  Doc5.pdf   text paginas=10 trechos= 22  -> polia
  Doc6.pdf   text paginas=10 trechos= 21  -> cocked_rotor

trechos        124
```

---

## Passo 8 — Conferir tudo

```powershell
python manage.py check
```

Tudo pronto quando as cinco linhas estiverem `ok`:

```
ok  banco         localhost:5433/prescritiva
ok  eventos       166.796
ok  scaler        scaler.joblib (16d)
ok  llm           deepseek/deepseek-v4-flash
ok  autenticacao  segredos configurados
```

---

## Passo 9 — Subir a API

```powershell
python manage.py runserver
```

Abra **http://127.0.0.1:8001** — cai direto no Swagger.

> Porta **8001**, não 8000. A 8000 costuma estar ocupada por outro projeto Python.
> Se estiver em uso, o uvicorn falha com `[Errno 10048]` e sai — mas
> `localhost:8000` continua respondendo, com o serviço do outro projeto.

Durante o desenvolvimento, use `--reload` para recarregar ao salvar:

```powershell
python manage.py runserver --reload
```

> **Sem `--reload`, o servidor não vê mudança de código.** Um servidor deixado no ar
> de uma sessão anterior continua servindo a versão antiga: rotas novas respondem
> `404` enquanto `/api/health` responde normalmente — parece bug, é servidor velho.
> Pare com `Ctrl+C` e suba de novo, ou use `--reload`.
>
> Para descobrir quem está segurando a porta:
> ```powershell
> Get-NetTCPConnection -LocalPort 8001 -State Listen | Select-Object OwningProcess
> ```

---

## Testar a API

Os endpoints internos exigem o cabeçalho `X-Internal-Key`, com o valor de
`INTERNAL_API_KEY` do `.env`. No Swagger, use o botão **Authorize**.

Pelo PowerShell, em outro terminal:

```powershell
$chave = (Select-String -Path backend\.env -Pattern '^INTERNAL_API_KEY=(.+)$').Matches.Groups[1].Value
$h = @{ "X-Internal-Key" = $chave }

# Estado do sistema (não exige autenticação)
Invoke-RestMethod http://127.0.0.1:8001/api/health | ConvertTo-Json -Depth 4

# Puxa um evento real do holdout (dado que o modelo nunca viu)
$evento = Invoke-RestMethod http://127.0.0.1:8001/api/internal/events/sample -Headers $h
$evento | ConvertTo-Json

# Analisa esse evento
$r = Invoke-RestMethod http://127.0.0.1:8001/api/internal/events/similar `
     -Method Post -Headers $h -ContentType "application/json" `
     -Body ($evento | ConvertTo-Json)

"real:      $($evento.fault_family)"
"diagnóstico: $($r.familia_diagnosticada)  confiança: $($r.confianca)"
$r.votos | Select-Object -First 3
```

---

## Testes automatizados

```powershell
cd backend
pytest -q                              # 80 testes
ruff check . ; ruff format --check .   # lint
```

Os testes de integração são pulados automaticamente se o banco não estiver no ar.

---

## Relatórios de análise

Regeneram os documentos de `backend/docs/analise/` a partir dos dados reais:

```powershell
python manage.py report                # todos
python manage.py report taxonomia      # 151 rótulos -> 14 famílias
python manage.py report similaridade   # acurácia no holdout, precisão x cobertura
python manage.py report documentos     # base documental e cobertura de falhas
```

---

## Operar o banco

```powershell
docker compose ps                      # estado
docker compose logs -f db              # logs
docker compose down                    # para, mantendo os dados
docker compose down -v                 # para e APAGA os dados
python manage.py initdb --drop         # recria o schema do zero
```

Inspecionar direto:

```powershell
docker exec -it prescritiva-db psql -U prescritiva -d prescritiva
```

```sql
\dt                                          -- tabelas
\di *hnsw*                                   -- índices vetoriais
SELECT fault_family, count(*) FROM sensor_events GROUP BY 1 ORDER BY 2 DESC;
SELECT filename, pages, extraction_method FROM documents;
```

---

## Console interativo

REPL com sessão e modelos já carregados:

```powershell
python manage.py shell
```

```python
from sqlalchemy import select, func

session.scalar(select(func.count()).select_from(SensorEvent))
```

---

## Se algo der errado

| Sintoma | Causa | Solução |
| --- | --- | --- |
| `RuntimeError: Variaveis de autenticacao ausentes` | `.env` sem os segredos | Passo 3 |
| `[Errno 10048] error while attempting to bind` | Porta 8001 ocupada | `python manage.py runserver --port 8002` |
| `sem conexao com o PostgreSQL` | Container parado | `docker compose up -d db` |
| `scaler.joblib nao encontrado` | Ingestão não rodou | Passo 6 |
| `CREATE EXTENSION vector` falha | Imagem errada do Postgres | Use `pgvector/pgvector:pg17` |
| `Activate.ps1 cannot be loaded` | Política de execução | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| Rota nova responde `404`, mas `/api/health` funciona | Servidor antigo ainda no ar | `Ctrl+C` e subir de novo, ou usar `--reload` |
| `network prescritiva-net not found` | Rede não criada | `docker network create prescritiva-net` |
| LLM responde `429 insufficient_quota` | Conta sem crédito | Troque o provider no `.env` |

---

## Resumo — do zero ao ar

```powershell
# raiz do projeto
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd backend
Copy-Item .env.example .env
python manage.py secrets        # cole a saída no .env, junto da LLM_API_KEY

docker network create prescritiva-net
docker compose up -d db

python manage.py initdb
python manage.py ingest
python manage.py ingest-docs
python manage.py check
python manage.py runserver      # http://127.0.0.1:8001
```
