# Comandos

Todos rodam a partir de `backend/`, com a venv ativa.

## Primeira execução

```powershell
# 1. Segredos de autenticação (a API nao sobe sem eles -- por desenho)
python manage.py secrets
# cole a saida em backend/.env; a INTERNAL_API_KEY vai tambem em frontend/.env

# 2. Banco PostgreSQL + pgvector (container Docker local, porta 5433)
docker network create prescritiva-net
docker compose up -d db

# 3. Schema e dados
python manage.py initdb        # CREATE EXTENSION vector + tabelas + indices HNSW
python manage.py ingest        # ~167 mil registros, alguns minutos
```

## Criar o banco PostgreSQL + pgvector

O jeito recomendado e o `docker compose up -d db` acima: ele ja traz usuario, senha,
volume nomeado e healthcheck, e a porta 5433 (para nao colidir com um PostgreSQL
instalado na 5432).

```powershell
docker network create prescritiva-net     # so na primeira vez
docker compose up -d db
docker compose ps                         # aguarde ficar "healthy"
```

### Sem compose, com `docker run`

Equivalente manual, caso queira subir o container avulso:

```powershell
docker run -d `
  --name prescritiva-db `
  --network prescritiva-net `
  -e POSTGRES_USER=prescritiva `
  -e POSTGRES_PASSWORD=prescritiva `
  -e POSTGRES_DB=prescritiva `
  -p 5433:5432 `
  -v pgdata_prescritiva:/var/lib/postgresql/data `
  --health-cmd="pg_isready -U prescritiva -d prescritiva" `
  --health-interval=5s `
  pgvector/pgvector:pg17
```

> A imagem e a `pgvector/pgvector:pg17` -- PostgreSQL 17 com a extensao ja compilada.
> Uma imagem `postgres:17` comum **nao** serve: `CREATE EXTENSION vector` falha porque
> a extensao nao esta instalada.

### Habilitar a extensao

`python manage.py initdb` ja executa `CREATE EXTENSION IF NOT EXISTS vector` antes de
criar as tabelas -- a extensao precisa existir para as colunas `vector(16)` e
`vector(384)` serem criadas. Para fazer na mao:

```powershell
docker exec -it prescritiva-db psql -U prescritiva -d prescritiva -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec -it prescritiva-db psql -U prescritiva -d prescritiva -c "SELECT extversion FROM pg_extension WHERE extname='vector';"
```

### Conferir

```powershell
python manage.py check
docker exec -it prescritiva-db psql -U prescritiva -d prescritiva -c "\dt"
docker exec -it prescritiva-db psql -U prescritiva -d prescritiva -c "\di *hnsw*"
```

## Dia a dia

```powershell
python manage.py check                 # banco, dados, scaler, LLM, segredos
python manage.py runserver --reload    # http://127.0.0.1:8001/docs
python manage.py report                # relatorios em docs/analise/
python manage.py shell                 # REPL com session e modelos
pytest -q
ruff check . && ruff format .
```

## Executar a aplicação ASGI direto

`manage.py runserver` e um atalho para o uvicorn. O equivalente explicito:

```powershell
uvicorn app.main:app --port 8001 --reload
```

> **Porta 8001, nao 8000.** A 8000 costuma estar ocupada por outro projeto Python na
> maquina. Mesmo motivo da 5433 no PostgreSQL. Se a porta estiver em uso, o uvicorn
> falha com `[Errno 10048]` e qualquer resposta em `localhost:8000` vem do outro servico.

## Banco

```powershell
docker compose ps                      # estado do container
docker compose logs -f db
docker compose down                    # para (mantem o volume)
docker compose down -v                 # para e APAGA os dados
python manage.py initdb --drop         # recria o schema do zero
```

## Erros comuns

| Sintoma | Causa | Solucao |
| --- | --- | --- |
| `RuntimeError: Variaveis de autenticacao ausentes` | `.env` sem os segredos | `python manage.py secrets` e preencher `backend/.env` |
| `[Errno 10048] error while attempting to bind` | Porta ja em uso | Usar `--port 8001` ou liberar a porta |
| `scaler.joblib nao encontrado` | Ingestao nao rodou | `python manage.py ingest` |
| `sem conexao com o PostgreSQL` | Container parado | `docker compose up -d db` |
