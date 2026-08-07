# Manutenção Preditiva com IA — Chão de Fábrica

Solução para o estudo de caso do **Processo Seletivo 02198/2026 — Desenvolvedor Full Stack
Pleno (IA e Python)**, FIESC / SENAI SC.

---

## 1. O desafio

Uma indústria de grande porte de Santa Catarina monitora máquinas rotativas com sensores de
vibração. Hoje ela consegue prever *quando* um equipamento vai falhar. Quer ir além: saber
**o que fazer para corrigir** — manutenção **prescritiva**.

O enunciado pede um pipeline completo de IA que, ao receber um novo evento de sensor:

1. **Encontre eventos históricos com comportamento semelhante** — sem depender de
   classificação prévia de falhas conhecidas, e sim de busca por similaridade no histórico.
2. **Informe o contexto**: quantos eventos parecidos já ocorreram, como se distribuem no
   tempo, com que frequência e em que condição operacional.
3. **Consulte a base documental da empresa** (manuais, procedimentos, relatórios técnicos)
   e sugira ações de inspeção, manutenção ou correção.
4. **Se restrinja ao que está documentado.** Sem documento para o problema identificado, o
   sistema deve informar isso e sugerir que o usuário registre um novo documento — em vez de
   inventar um procedimento.
5. **Apresente os resultados visualmente**: dashboards, gráficos e interação por chat.

### Restrições do enunciado

| Restrição | Como é atendida |
| --- | --- |
| Linguagem Python | Todo o backend, ETL, ML e RAG |
| Inferência em estação com até 32 GB RAM e GPU de 16 GB | Embeddings locais em ONNX (CPU, sem GPU); busca vetorial em PostgreSQL; camada de LLM isolada atrás de uma interface, com o caminho para modelo local documentado |

### Diferenciais previstos no enunciado

APIs · Bancos de Dados · Dashboards · Soluções de Deploy · Integrações em ambiente industrial —
todos contemplados na arquitetura.

### Dados fornecidos

| Arquivo | Conteúdo |
| --- | --- |
| `dados/banner.csv` | 166.796 registros de sensores de vibração (eixos X e Z), 151 rótulos brutos na coluna `fault` |
| `arquivos/Doc1..Doc6.pdf` | Documentação de falhas da empresa |

---

## 2. O que a exploração dos dados revelou

Três achados moldaram a arquitetura. Nenhum estava no enunciado.

### 2.1 Os 151 rótulos são, na verdade, 14 famílias

A coluna `fault` foi preenchida manualmente por operadores. O ruído tem três origens:

- **Sufixos de sessão de ensaio** — `_2`, `_carga`, `_adxl_0`, `_pos_2`, prefixo `new_`.
  Indicam repetição do ensaio, mudança de carga ou troca de acelerômetro, não uma falha diferente.
- **Erros de digitação** — `desabalanceado_3`, `desbanlanceado_carga_3_2`,
  `ddesbalanceado_adxl_0`, `mortor_desligado_novo`, `normla_carga_3_3`, `cockecocked_adxl_0`.
- **Estados que não são problemas** — `normal`, `baseline`, `teste`, `acelerando`,
  `motor_desligado`, conforme a seção 6 do enunciado.

Sem normalizar isso, toda contagem de "eventos similares" nasce errada. A taxonomia canônica
mapeia **151/151 rótulos, zero desconhecidos**:

| Família | Registros | % | Problema |
| --- | ---: | ---: | :---: |
| `rolamento` | 60.779 | 36,4% | sim |
| `eccentric_rotor` | 16.497 | 9,9% | sim |
| `normal` | 15.058 | 9,0% | não |
| `cocked_rotor` | 14.275 | 8,6% | sim |
| `desbalanceamento` | 13.237 | 7,9% | sim |
| `ventoinha` | 12.299 | 7,4% | sim |
| `polia` | 12.000 | 7,2% | sim |
| `correia` | 11.999 | 7,2% | sim |
| `desalinhamento` | 9.178 | 5,5% | sim |
| `falta_fase` | 800 | 0,5% | sim |
| `motor_desligado` | 497 | 0,3% | não |
| `teste` | 101 | 0,1% | não |
| `baseline` | 69 | 0,0% | não |
| `acelerando` | 7 | 0,0% | não |

Matriz completa em [`backend/docs/analise/taxonomia.md`](backend/docs/analise/taxonomia.md).

### 2.2 Cinco colunas são a mesma grandeza em outra unidade

Auditoria sobre os 166.796 registros:

| Par | Correlação | Razão |
| --- | ---: | ---: |
| `z_rms_velocity_in_s` × `z_rms_velocity_mm_s` | 0,999999 | 25,4114 |
| `x_rms_velocity_in_s` × `x_rms_velocity_mm_s` | 0,999999 | 25,4079 |
| `z_peak_velocity_in_s` × `z_peak_velocity_mm_s` | 1,000000 | 25,4081 |
| `x_peak_velocity_in_s` × `x_peak_velocity_mm_s` | 1,000000 | 25,4056 |
| `temperature_f` × `temperature_c` | 0,999999 | relação afim |

E há uma redundância pior, que não é de unidade: **`peak_velocity` é uma coluna derivada, não
medida.**

| Par | Correlação | Razão |
| --- | ---: | ---: |
| `z_rms_velocity_mm_s` × `z_peak_velocity_mm_s` | 1,000000 | 1,414334 |
| `x_rms_velocity_mm_s` × `x_peak_velocity_mm_s` | 1,000000 | 1,414297 |

A razão é √2 = 1,414214, com desvio da ordem de 10⁻⁴. O firmware do sensor calcula o pico de
velocidade a partir do RMS assumindo sinal senoidal — a coluna não carrega nenhuma informação
além do RMS.

Mantê-las daria peso dobrado a velocidade e temperatura no cálculo de distância. As colunas
métricas ainda têm mais precisão armazenada (`mm_s` tem 3.568 valores distintos contra 1.954
em `in_s` — o valor imperial é o arredondado). Vetor final: **16 dimensões**; as derivadas
seguem persistidas para exibição, apenas fora do vetor.

### 2.3 O dataset traz um holdout temporal pronto

Todo rótulo com prefixo `new_` foi coletado entre **10 e 16/jun/2026**; todo o restante é de
até **09/jun**. Isso vira o conjunto de teste sem precisar sortear nada — e sortear seria um
erro grave: amostras da mesma sessão de ensaio foram coletadas com segundos de diferença e
cairiam dos dois lados, inflando a acurácia.

| Split | Registros | Período |
| --- | ---: | --- |
| `train` | 157.735 | 30/04/2026 a 09/06/2026 |
| `holdout` | 9.061 | 10/06/2026 a 16/06/2026 |

A regra é **verificada contra as datas reais** durante a ingestão, não assumida pelo nome:
divergência entre prefixo e data aborta a carga.

### 2.4 Um dos documentos não tem texto

`Doc1.pdf` tem 17 páginas e **zero caractere extraível** — é um documento Word com imagens
coladas. Doc2 a Doc6 têm camada de texto e cobrem, respectivamente: desalinhamento,
desbalanceamento, correias, polias e cocked rotor.

Isso significa que `rolamento` — a maior família do dataset, 36% dos registros — pode não ter
documentação legível. Se o OCR do Doc1 não a cobrir, o caso de recusa exigido pelo enunciado
("reportar que ainda não existe o problema identificado") é **real**, não fabricado para a
demonstração.

---

## 3. Arquitetura

```
        Sensores de vibração (chão de fábrica)
                      │
                      ▼
       ┌──────────────────────────┐
       │  API — FastAPI           │
       │                          │
       │  externa  /api/v1        │◄── JWT Bearer ──── CMMS, supervisório, coletor
       │  interna  /api/internal  │◄── X-Internal-Key ── frontend (via proxy)
       └────────────┬─────────────┘
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
  Motor de      Gate de        Camada LLM
similaridade   cobertura      (OpenAI / DeepSeek,
     │        documental       trocável por local)
     │              │              │
     └──────────────┴──────────────┘
                    │
        ┌───────────▼──────────────┐
        │ PostgreSQL 17 + pgvector │
        │                          │
        │ sensor_events    (18-d)  │  ← similaridade de sinal
        │ document_chunks  (384-d) │  ← RAG documental
        │ fault_document_coverage  │  ← regra de recusa
        └──────────────────────────┘
```

### Decisões e por quê

| Decisão | Motivo |
| --- | --- |
| **Um banco só (PostgreSQL + pgvector)** para vetor de sensor e embedding de documento | 167 mil vetores de 18-d e algumas centenas de chunks não justificam um banco vetorial dedicado; e permite cruzar vizinhança de sensor com metadado de falha em uma consulta SQL |
| **Busca por similaridade, não classificador** | O enunciado é explícito: a solução não depende de classificação prévia de falhas conhecidas. Um classificador também não responderia "quantos eventos parecidos já ocorreram" |
| **Índice HNSW parcial (`WHERE split='train'`)** | O HNSW faz pós-filtro: busca os k vizinhos e só depois aplica o `WHERE`. Partindo de um evento do holdout, os vizinhos mais próximos são do próprio holdout, o filtro descarta todos e a busca **retorna vazio** — comprovado durante a implementação. Como buscar no holdout seria vazamento, o filtro entra no índice |
| **Embeddings locais (fastembed / ONNX)** | Sem GPU, sem rede, ~50 MB de dependência em vez de ~2,5 GB do PyTorch. Sustenta a restrição de operar na workstation |
| **Gate de cobertura em código, antes do LLM** | "Só responder o que está documentado" é regra de negócio, não pedido educado no prompt. Sem documento, o modelo **não é chamado** — não há como alucinar o que não foi perguntado |
| **Compose separado por aplicação** | Backend e frontend têm ciclos de vida independentes; um compose único obrigaria a derrubar o banco para publicar a interface |
| **Duas superfícies de API, autenticações diferentes** | `/upload_doc` escreve na base que orienta intervenção física em equipamento. Escopo por endpoint impede que um integrador somente-leitura injete documento |

### Stack

| Camada | Tecnologia |
| --- | --- |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2 |
| Banco | PostgreSQL 17 + pgvector (HNSW, distância cosseno) |
| ML | scikit-learn (StandardScaler), busca KNN no pgvector |
| Embeddings | fastembed / ONNX Runtime, `multilingual-e5-small` (384-d), CPU |
| LLM | OpenAI ou DeepSeek — mesmo protocolo, trocável por `.env` |
| Frontend | React 19, TypeScript, Vite, TanStack Query, Recharts |
| Deploy | Docker Compose (um por aplicação), rede externa compartilhada |

---

## 4. API

### Externa — `/api/v1` (JWT no cabeçalho `Authorization`)

| Método | Rota | Escopo | Função |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/token` | — | Troca `client_id`/`client_secret` por um JWT |
| `POST` | `/api/v1/predict` | `predict` | JSON de métricas do sensor → motor de similaridade → busca no banco vetorial → LLM → JSON consolidado |
| `POST` | `/api/v1/upload_doc` | `upload` | Envia documento orientativo, processa e injeta no banco vetorial |
| `POST` | `/api/v1/events` | `ingest` | Recebe leituras do coletor e grava na base de análise |

`/api/v1/events` fecha o ciclo da Figura 01: o supervisório envia a leitura assim que ela
acontece, e ela passa a fazer parte do histórico consultado nas próximas análises. Aceita uma
leitura ou um lote, no formato exato do exemplo da seção 2 do enunciado.

Leitura sem `fault`, ou com rótulo fora da taxonomia, **é gravada mesmo assim** — a medição do
sensor vale mais que a anotação. Ela entra no histórico mas não participa da votação, e o
rótulo desconhecido volta na resposta para alguém decidir se vira família nova.

### Interna — `/api/internal` (cabeçalho `X-Internal-Key`)

Consumida apenas pelo frontend. A chave vive no proxy do container do frontend e **nunca chega
ao navegador**.

| Rota | Função |
| --- | --- |
| `POST /events/analyze` | Mesmo pipeline do `predict`, sem JWT |
| `POST /events/similar` | Só a similaridade, sem passar pelo modelo |
| `GET /events/sample` | Amostra do holdout, filtrável por família e por desfecho |
| `POST /chat` | Conversa ancorada num evento, sujeita ao mesmo gate de cobertura |
| `GET /stats/overview` | KPIs do painel numa chamada |
| `GET /stats/timeline` | Ocorrências por dia e por família |
| `GET /stats/distribution` | Faixa de valores de uma métrica em cada família |
| `GET /stats/frequency` | Recorrência: dias com ocorrência e intervalo médio |
| `GET /faults` | Famílias canônicas com estado de cobertura documental |
| `GET`/`POST` `/documents` | Lista e cadastra documento orientativo |

---

## 5. Como rodar

**Pré-requisitos:** Python 3.13 · Docker · Node 20+

```bash
# 1. Ambiente
python -m venv .venv
.venv\Scripts\activate                  # Windows
pip install -r backend/requirements.txt

# 2. Configuração
copy backend\.env.example backend\.env
cd backend
python manage.py secrets                # gera JWT_SECRET, credenciais e chave interna
# cole os segredos em backend/.env e preencha LLM_API_KEY

# 3. Banco
docker network create prescritiva-net
docker compose -f docker-compose.yml up -d db

# 4. Schema e dados
python manage.py initdb
python manage.py ingest                 # ~167 mil registros
python manage.py report                 # relatórios de análise

# 5. Verificação e execução
python manage.py check                  # banco, dados, scaler, LLM, segredos
python manage.py runserver --reload     # http://127.0.0.1:8001/docs
pytest -q
```

### `manage.py`

FastAPI não tem um `manage.py` embutido como o Django. Este arquivo cumpre o mesmo papel:
reunir as tarefas administrativas em um comando só, em vez de espalhar `python -m ...` pela
documentação.

| Comando | Função |
| --- | --- |
| `runserver` | Sobe a API (uvicorn) |
| `initdb` | Cria extensão, tabelas e índices (idempotente) |
| `ingest` | Ingere `dados/banner.csv` |
| `secrets` | Gera segredos de autenticação |
| `report` | Gera os relatórios de análise |
| `check` | Verifica configuração, banco, dados e artefatos |
| `shell` | REPL com sessão e modelos carregados |

> `manage.py` **não** é `app/main.py`. `main.py` é o objeto ASGI que o uvicorn **importa**
> (`uvicorn app.main:app`) — precisa ser importável sem efeito colateral, já que cada worker
> o carrega. `manage.py` é uma CLI que você **executa**. Juntá-los faria todo worker HTTP
> carregar o parser de argumentos, e `python main.py ingest` construiria a aplicação inteira
> só para rodar um ETL.

---

## 6. Organização do repositório

```
├── backend/
│   ├── manage.py               # CLI administrativa
│   ├── app/
│   │   ├── main.py             # fábrica da aplicação ASGI
│   │   ├── settings/           # configuração via .env (pydantic-settings)
│   │   ├── database/           # base declarativa, engine e sessão
│   │   ├── models/             # entidades — um arquivo por tabela
│   │   ├── schemas/            # contratos de entrada e saída da API
│   │   ├── repositories/       # acesso a dados — todas as consultas
│   │   ├── services/           # regra de negócio: similaridade, RAG, cobertura
│   │   ├── controllers/
│   │   │   ├── health.py       # público
│   │   │   ├── v1/             # externo — JWT Bearer
│   │   │   └── internal/       # interno — X-Internal-Key
│   │   ├── core/               # domínio puro, sem I/O
│   │   │   ├── taxonomy.py     # 151 rótulos → 14 famílias
│   │   │   └── features.py     # vetor de 18 dimensões + scaler
│   │   ├── integrations/       # fronteiras externas: LLM, embeddings, OCR
│   │   ├── middleware/
│   │   └── security/           # JWT externo + chave interna
│   ├── scripts/                # ETL e relatórios, invocados pelo manage.py
│   ├── docs/
│   │   ├── README.md           # índice de specs com status
│   │   ├── SPEC-FEAT-XXX/      # spec.md + acceptance.md + tasks.md
│   │   └── analise/            # relatórios gerados a partir dos dados
│   ├── tests/
│   ├── docker-compose.yml      # db + api
│   └── requirements.txt
├── frontend/
│   ├── docs/                   # specs do frontend, mesmo padrão
│   └── docker-compose.yml      # web
├── tools/specs/                # catálogo das specs e gerador de status
├── dados/                      # banner.csv
└── arquivos/                   # Doc1..Doc6.pdf
```

### Camadas

Padrão MVC adaptado a uma API, com uma regra que mantém a separação honesta:
**um controller nunca monta consulta SQL, e um repositório nunca chama LLM.**

| Camada | Papel | Depende de |
| --- | --- | --- |
| `controllers/` | Traduz requisição HTTP em chamada de serviço. Autenticação e validação. | services, schemas |
| `services/` | Regra de negócio: similaridade, gate de cobertura, RAG, prescrição. | repositories, core, integrations |
| `repositories/` | Todas as consultas ao banco. | models, database |
| `models/` | Entidades e schema (Model). | database |
| `schemas/` | Contratos de entrada e saída (View). | — |
| `core/` | Domínio puro: taxonomia e features. Sem I/O, testável isolado. | — |
| `integrations/` | Fronteiras externas: LLM, embeddings, OCR. | settings |

### Método: spec-driven

Cada feature tem uma pasta `SPEC-FEAT-XXX/` com três arquivos:

- **`spec.md`** — contexto, escopo, fora de escopo, decisões técnicas e contrato
- **`acceptance.md`** — critérios de aceite, cada um com seu método de verificação
- **`tasks.md`** — tarefas executáveis

O status **não é escrito à mão**: `tools/specs/gen.py` conta os checkboxes e reconstrói o
índice. Uma feature só é dada como concluída quando tarefas **e** critérios de aceite estão
marcados — e um critério só é marcado após verificação prática.

| App | Features | Índice |
| --- | ---: | --- |
| Backend | 16 | [`backend/docs/README.md`](backend/docs/README.md) |
| Frontend | 8 | [`frontend/docs/README.md`](frontend/docs/README.md) |

---

## 7. Estado atual

| Marco | Conteúdo | Situação |
| --- | --- | --- |
| **M1** | Infra, taxonomia, features, ingestão | concluído |
| **M2** | OCR, indexação documental, gate de cobertura | concluído |
| **M3** | Similaridade calibrada, RAG, geração, antialucinação | concluído |
| **M4** | API completa, upload de documento, frontend | concluído |
| **M5** | Documentação de arquitetura, roteiro de demonstração | concluído |

O andamento por feature não é escrito à mão: sai da contagem de checkboxes em
[`backend/docs/README.md`](backend/docs/README.md) (17 features) e
[`frontend/docs/README.md`](frontend/docs/README.md) (8 features).

A arquitetura de implantação industrial — segmentação de rede ISA-95, dimensionamento,
degradação, ciclo de vida do modelo e alternativas descartadas — está em
[`ARQUITETURA.md`](ARQUITETURA.md). O passo a passo da demonstração, com os números
conferidos contra o sistema rodando, está em [`ROTEIRO.md`](ROTEIRO.md).

---

## 8. O resultado do motor de similaridade

Reportado como medido. Relatório completo e reproduzível em
[`backend/docs/analise/similaridade.md`](backend/docs/analise/similaridade.md)
(`python manage.py report similaridade`).

**Acurácia bruta no holdout: 40,2%** sobre 3.000 eventos. Três investigações explicam o número
e definem o desenho da solução.

### `falta_fase` não tem histórico

800 registros no holdout, **zero no treino**. Nenhuma busca por similaridade poderia acertá-la.
O comportamento correto não é adivinhar — é recusar. O mesmo vale para `baseline` (69 eventos).

### O teto é dos dados, não do método

| Modelo | Treino | Holdout |
| --- | ---: | ---: |
| KNN por similaridade (k=50) | — | 40,2% |
| HistGradientBoosting (200 iterações) | 78,8% | 39,8% |

Um classificador supervisionado chega exatamente ao mesmo lugar. Existe deslocamento de
distribuição real entre o histórico e as sessões `new_*`: as médias padronizadas da família
`rolamento` deslocam 0,45 desvios em média (1,46 na temperatura), e o holdout opera em um
regime de RPM praticamente ausente do histórico.

### Distância é um péssimo sinal de confiança

Foi a descoberta que mudou o desenho. O plano original era usar distância ao vizinho mais
próximo como detector de fora de distribuição. A medição mostrou o oposto do esperado:

| Portão | Cobertura | Precisão |
| --- | ---: | ---: |
| sem portão | 100% | 40,2% |
| distância ≤ 0,5 | 13% | **18,4%** |
| concordância ≥ 0,70 | 46,7% | 59,2% |
| concordância ≥ 0,95 | 19,2% | **73,4%** |

Quanto *mais próximo* o vizinho, *pior* a precisão. Os vizinhos mais próximos caem no cluster
dominante de `rolamento` (36% do histórico) — proximidade alta muitas vezes significa absorção
pela classe majoritária. Ter seguido o plano original produziria alta confiança exatamente nos
casos mais enviesados.

O sinal que funciona é a **concordância da vizinhança**. É o que o sistema usa.

### Por isso a abstenção é o comportamento correto

Prescrever intervenção física em equipamento com 40% de acerto é pior que admitir
desconhecimento. Com o limiar configurado (0,70), o sistema diagnostica 47% dos casos a 59% de
precisão e se abstém no resto — entregando mesmo assim os eventos similares, a distribuição
temporal e o contexto operacional para análise humana. E recusa 59% dos eventos de
`falta_fase`, a família que não tem como acertar.

O limiar é uma escolha explícita e mensurável, ajustável em `SIMILARITY_CONFIDENCE_MIN`.
