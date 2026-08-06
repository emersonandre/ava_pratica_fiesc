# Estrutura do Projeto

Manutenção Prescritiva com IA — FIESC / SENAI SC, processo seletivo 02198/2026.

Documento de referência da organização de pastas. Contexto do desafio, decisões e como rodar
estão no [README.md](README.md).

**Legenda:** ✅ implementado · 🔜 planejado (spec escrita, código pendente)

---

## 1. Stack

| Camada | Tecnologia |
| --- | --- |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2 — **app ASGI nativo, não Django** |
| Banco | PostgreSQL 17 + pgvector (HNSW, distância cosseno) |
| ML | scikit-learn (StandardScaler), busca KNN no pgvector |
| Embeddings | fastembed / ONNX Runtime, `multilingual-e5-small` (384-d), CPU |
| LLM | OpenAI ou DeepSeek — mesmo protocolo, trocável por `.env` |
| Frontend | React 19, TypeScript, Vite, TanStack Query, Recharts |
| Deploy | Docker Compose — **um por aplicação**, rede externa `prescritiva-net` |

---

## 2. Raiz

```
ava_pratica_fiesc/
├── backend/                # API, ETL, ML e RAG
├── frontend/               # Interface web
├── dados/
│   ├── banner.csv          # 166.796 registros de sensor (versionado)
│   └── banner.xlsx         # mesma base em Excel (fora do Git — duplicata de 20 MB)
├── arquivos/
│   └── Doc1..Doc6.pdf      # documentação de falhas fornecida pela empresa
├── tools/specs/            # catálogo das specs e gerador de status
├── estrutura.md            # este documento
├── ARQUITETURA.md          # arquitetura de solução e de implantação industrial
├── ROTEIRO.md              # passo a passo da demonstração
├── commands.md             # passo a passo para subir e testar
├── README.md               # visão geral, decisões e execução
└── .gitignore
```

Não há `docker-compose.yml` na raiz — cada aplicação tem o seu.

---

## 3. Backend

```
backend/
├── manage.py                    ✅ CLI administrativa
├── pyproject.toml               ✅ pytest + ruff
├── requirements.txt             ✅ dependências
├── requirements.lock.txt        ✅ versões exatas (pip freeze)
├── docker-compose.yml           ✅ serviços db + api
├── Dockerfile                   🔜
├── .env.example                 ✅ todas as variáveis documentadas
├── commands.md                  ✅ comandos de uso rápido
│
├── app/
│   ├── main.py                  ✅ fábrica da aplicação ASGI (create_app)
│   │
│   ├── settings/                ✅ configuração
│   │   ├── __init__.py          #   exporta Settings, get_settings, PROJECT_ROOT
│   │   └── config.py            #   pydantic-settings, validação na inicialização
│   │
│   ├── database/                ✅ persistência
│   │   ├── __init__.py
│   │   ├── base.py              #   DeclarativeBase isolada (quebra ciclo de import)
│   │   └── session.py           #   engine, session_scope, get_session, ping
│   │
│   ├── models/                  ✅ entidades — um arquivo por tabela
│   │   ├── __init__.py          #   agrega tudo no Base.metadata
│   │   ├── sensor_event.py      #   sensor_events + índice HNSW parcial (18-d)
│   │   ├── document.py          #   documents
│   │   ├── document_chunk.py    #   document_chunks + índice HNSW (384-d)
│   │   ├── fault_coverage.py    #   fault_document_coverage — sustenta o gate
│   │   └── index_metadata.py    #   modelo e dimensão do índice vetorial
│   │
│   ├── schemas/                 ✅ contratos de entrada e saída da API
│   │   ├── __init__.py
│   │   ├── health.py            ✅
│   │   ├── sensor_event.py      🔜 payload do §2 do enunciado
│   │   ├── similarity.py        🔜 vizinhos, contagens, timeline, contexto
│   │   ├── prescription.py      🔜 diagnóstico, inspeção, correção, citações
│   │   └── document.py          🔜 upload e listagem
│   │
│   ├── repositories/            🔜 acesso a dados — todas as consultas
│   │   ├── sensor_event.py      #   KNN e agregações
│   │   ├── document.py
│   │   └── coverage.py
│   │
│   ├── services/                🔜 regra de negócio
│   │   ├── similarity.py        #   voto ponderado, confiança, fora de distribuição
│   │   ├── coverage.py          #   gate determinístico — roda ANTES do LLM
│   │   ├── retrieval.py         #   busca híbrida filtrada por família
│   │   ├── prescription.py      #   geração estruturada com citações
│   │   ├── grounding.py         #   verificação de embasamento pós-geração
│   │   └── ingestion.py         #   pipeline de documento novo
│   │
│   ├── controllers/             rotas HTTP
│   │   ├── health.py            ✅ /api/health — verificação real de cada componente
│   │   ├── v1/                  🔜 superfície externa — JWT Bearer
│   │   │   ├── auth.py          #   POST /api/v1/auth/token
│   │   │   ├── predict.py       #   POST /api/v1/predict
│   │   │   └── upload_doc.py    #   POST /api/v1/upload_doc
│   │   └── internal/            🔜 superfície interna — X-Internal-Key
│   │       ├── events.py        #   similar, sample
│   │       ├── chat.py
│   │       ├── stats.py         #   overview, timeline
│   │       └── documents.py
│   │
│   ├── core/                    ✅ domínio puro — sem I/O, testável isolado
│   │   ├── taxonomy.py          #   151 rótulos → 14 famílias
│   │   └── features.py          #   vetor de 18 dimensões + scaler
│   │
│   ├── integrations/            🔜 fronteiras externas
│   │   ├── llm.py               #   provider OpenAI/DeepSeek
│   │   ├── embeddings.py        #   fastembed / ONNX
│   │   └── ocr.py               #   Doc1: 17 páginas sem camada de texto
│   │
│   ├── middleware/              🔜 tempo por etapa, log estruturado
│   │
│   └── security/                ✅ autenticação
│       ├── __init__.py
│       └── tokens.py            #   JWT com escopos + chave interna
│
├── scripts/                     ✅ ETL e relatórios, invocados pelo manage.py
│   ├── init_db.py
│   ├── ingest_csv.py
│   ├── gen_secrets.py
│   └── report_taxonomy.py
│
├── tests/
│   ├── test_taxonomy.py         ✅ 55 testes
│   ├── test_features.py         🔜
│   ├── test_similarity.py       🔜
│   ├── test_coverage.py         🔜
│   ├── test_security.py         🔜
│   └── test_alucinacao.py       🔜 suíte adversarial
│
├── artifacts/                   fora do Git — scaler.joblib, cache de OCR
│
└── docs/
    ├── README.md                ✅ índice de specs com status calculado
    ├── SPEC-FEAT-001..016/      ✅ spec.md + acceptance.md + tasks.md
    └── analise/
        ├── taxonomia.md         ✅ matriz auditável dos 151 rótulos
        ├── features.md          🔜 auditoria de redundância
        ├── dataset.md           🔜 contagens e distribuição
        ├── documentos.md        🔜 resumo por PDF, resultado do OCR
        ├── cobertura.md         🔜 mapa família → documento
        ├── similaridade.md      🔜 matriz de confusão no holdout
        └── alucinacao.md        🔜 resultado da suíte adversarial
```

### Camadas

Padrão MVC adaptado a uma API. A regra que mantém a separação honesta:
**um controller nunca monta consulta SQL, e um repositório nunca chama LLM.**

| Camada | Papel | Pode depender de |
| --- | --- | --- |
| `controllers/` | Autenticação, validação, tradução de HTTP para serviço | services, schemas |
| `services/` | Regra de negócio: similaridade, gate, RAG, prescrição | repositories, core, integrations |
| `repositories/` | Todas as consultas ao banco | models, database |
| `models/` | Entidades e schema (**Model**) | database |
| `schemas/` | Contratos de entrada e saída (**View**) | — |
| `core/` | Domínio puro, sem I/O | — |
| `integrations/` | LLM, embeddings, OCR | settings |

### `manage.py` × `app/main.py`

Não são a mesma coisa e não podem ser o mesmo arquivo.

| | `app/main.py` | `manage.py` |
| --- | --- | --- |
| O que é | O objeto ASGI — a aplicação | CLI administrativa |
| Como é usado | Uvicorn **importa**: `uvicorn app.main:app` | Você **executa**: `python manage.py ingest` |
| Restrição | Precisa ser importável sem efeito colateral (cada worker o carrega) | — |

Juntá-los faria todo worker HTTP carregar o parser de argumentos, e `python main.py ingest`
construiria a aplicação inteira só para rodar um ETL.

FastAPI não traz um `manage.py` embutido como o Django. O arquivo existe para reunir as
tarefas administrativas em um comando só:

| Comando | Função |
| --- | --- |
| `runserver` | Sobe a API (uvicorn) |
| `initdb` | Cria extensão, tabelas e índices (idempotente) |
| `ingest` | Ingere `dados/banner.csv` |
| `secrets` | Gera segredos de autenticação |
| `report` | Gera os relatórios de análise |
| `check` | Verifica configuração, banco, dados e artefatos |
| `shell` | REPL com sessão e modelos carregados |

### Banco

| Tabela | Conteúdo |
| --- | --- |
| `sensor_events` | 166.796 registros + vetor `vector(18)`, índice HNSW **parcial** (`WHERE split='train'`) |
| `documents` | Documentos técnicos, método de extração (`text`/`ocr`), estado de indexação |
| `document_chunks` | Trechos + `vector(384)` + proveniência (documento, página, seção) |
| `fault_document_coverage` | Mapa família → documento — sustenta o gate de recusa |
| `index_metadata` | Modelo e dimensão do índice vetorial |

---

## 4. Frontend

React 19 + TypeScript + Vite. Sem framework de UI: os componentes são poucos e específicos,
e uma biblioteca genérica traria mais peso que proveito.

```
frontend/
├── docker-compose.yml           serviço web, rede externa compartilhada
├── Dockerfile                   multi-estágio: build Vite → nginx
├── nginx.conf.template          proxy que injeta X-Internal-Key
├── .env.example
├── package.json
├── vite.config.ts
├── tsconfig.json
│
├── src/
│   ├── main.tsx                 bootstrap, rotas e provider do TanStack Query
│   │
│   ├── api/
│   │   ├── client.ts            fetch com teto de espera e erro nomeado
│   │   ├── queries.ts           hooks do TanStack Query, um por endpoint
│   │   └── types.ts             tipos espelhando o contrato da API
│   │
│   ├── components/
│   │   ├── Layout.tsx           barra lateral, cabeçalho, saúde do sistema
│   │   ├── Estado.tsx           carregando, erro, vazio
│   │   └── Progresso.tsx        etapas do pipeline com peso proporcional
│   │
│   ├── features/
│   │   ├── painel/
│   │   │   ├── Painel.tsx       a regra do sistema, KPIs, tipos de falha
│   │   │   ├── LinhaDoTempo.tsx ocorrências por dia, com o corte do holdout
│   │   │   ├── Recorrencia.tsx  dias com ocorrência e intervalo médio
│   │   │   └── Separabilidade.tsx  faixa de valores por família
│   │   ├── analise/
│   │   │   ├── Analise.tsx      os quatro passos da análise
│   │   │   ├── ColarJson.tsx    entrada manual de leitura em JSON
│   │   │   ├── Prescricao.tsx   procedimento, citado passo a passo
│   │   │   ├── Chat.tsx         perguntas ancoradas no evento
│   │   │   ├── Citacoes.tsx     citação clicável e painel do trecho
│   │   │   └── Detalhes.tsx     vizinhos, votação e tempos por etapa
│   │   └── documentos/
│   │       └── Documentos.tsx   lista, upload e lacunas de cobertura
│   │
│   ├── lib/formato.ts           número, data, rótulo e cor de família
│   └── styles/
│       ├── tokens.css           paleta, tipografia, espaço, forma
│       └── base.css             reset e primitivas (cartão, distintivo, botão)
│
└── docs/
    ├── README.md                índice de specs com status
    └── SPEC-FEAT-001..008/      spec.md + acceptance.md + tasks.md
```

### Os quatro passos da análise

A tela de análise é a leitura do enunciado transformada em fluxo. Cada passo só aparece
quando o anterior conclui, e a ordem não é estética — é a do pipeline:

| Passo | O que acontece | Vem de |
| --- | --- | --- |
| 1 | Escolher a leitura: do holdout, por condição anotada, ou colando o JSON | `GET /events/sample` |
| 2 | Identificar a falha: votação dos 50 vizinhos e concordância | `POST /events/analyze` |
| 3 | Procedimento recomendado, ou a recusa explicando o motivo | mesmo endpoint, `gerar_prescricao` |
| 4 | Chat: perguntas de acompanhamento, sujeitas ao mesmo gate | `POST /chat` |

O passo 3 é onde a recusa aparece. Não é caminho de erro: é o comportamento correto quando a
família não tem documento, quando o padrão é operação normal, ou quando a vizinhança não
concorda o bastante.

### Chave interna nunca chega ao navegador

O navegador chama `/api/*` no próprio host do frontend. O nginx do container encaminha para
a API injetando o cabeçalho `X-Internal-Key`, lido do ambiente. Qualquer segredo embutido no
bundle é público — basta abrir o DevTools.

---

## 5. Deploy

Um compose por aplicação, unidos por rede externa. Backend e frontend têm ciclos de vida
independentes: publicar a interface não derruba o banco.

```bash
docker network create prescritiva-net                      # uma vez

docker compose -f backend/docker-compose.yml up -d         # db + api
docker compose -f frontend/docker-compose.yml up -d        # web
```

| Compose | Serviços | Porta no host |
| --- | --- | --- |
| `backend/docker-compose.yml` | `db` (pgvector/pg17), `api` | 5433, 8001 |
| `frontend/docker-compose.yml` | `web` (nginx) | 5173 |

---

## 6. API

### Externa — `/api/v1`, JWT `Bearer`

Consumida por sistemas da planta (CMMS, supervisório, coletor de dados).

| Método | Rota | Escopo |
| --- | --- | --- |
| `POST` | `/api/v1/auth/token` | — |
| `POST` | `/api/v1/predict` | `predict` |
| `POST` | `/api/v1/upload_doc` | `upload` |
| `POST` | `/api/v1/events` | `ingest` |

Escopo por endpoint: um integrador somente-leitura não injeta documento na base que orienta
intervenção física em equipamento, e o coletor que envia leitura não obtém prescrição.

`/api/v1/events` é a entrada automática da Figura 01: o supervisório grava a leitura no
histórico assim que ela acontece. Leitura sem `fault`, ou com rótulo fora da taxonomia, é
gravada mesmo assim — a medição vale mais que a anotação —, mas não participa da votação.

### Interna — `/api/internal`, cabeçalho `X-Internal-Key`

Consumida apenas pelo frontend: análise completa e similaridade isolada, chat, amostras do
holdout, estatísticas do painel (`overview`, `timeline`, `distribution`, `frequency`),
famílias com estado de cobertura e cadastro de documento.

### Pública

`GET /api/health` — estado real de banco, eventos, documentos, scaler e provider.

---

## 7. Método: spec-driven

Cada feature tem uma pasta com três arquivos:

```
docs/SPEC-FEAT-XXX/
├── spec.md          contexto, escopo, fora de escopo, decisões, contrato
├── acceptance.md    critérios de aceite, cada um com método de verificação
└── tasks.md         tarefas executáveis
```

As specs são geradas a partir de `tools/specs/catalog_backend.py` e `catalog_frontend.py`.
O status **não é escrito à mão**: `gen.py` conta os checkboxes e reconstrói o índice.

```bash
python tools/specs/gen.py                                     # regenera specs e índice
python tools/specs/mark.py backend SPEC-FEAT-002 tasks --all  # marca itens concluídos
```

Uma feature só é dada como concluída quando tarefas **e** critérios de aceite estão marcados —
e um critério só é marcado após verificação prática.

| App | Features | Índice |
| --- | ---: | --- |
| Backend | 17 | [`backend/docs/README.md`](backend/docs/README.md) |
| Frontend | 8 | [`frontend/docs/README.md`](frontend/docs/README.md) |
