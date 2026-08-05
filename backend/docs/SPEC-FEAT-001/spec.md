# SPEC-FEAT-001 — Infraestrutura local reproduzível

| | |
| --- | --- |
| **App** | backend |
| **Épico** | Infraestrutura e dados |
| **Atende** | DIF (Bancos de Dados, Soluções de Deploy) |
| **Depende de** | — |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

O projeto precisa subir na máquina do avaliador sem etapas manuais. Toda a persistência
— dados tabulares de sensor e vetores de embedding — fica em um único PostgreSQL com a
extensão `pgvector`, evitando um segundo serviço só para busca vetorial.

## Escopo

**Um `docker-compose.yml` por aplicação**, não um único na raiz:

| Arquivo | Serviços |
| --- | --- |
| `backend/docker-compose.yml` | `db` (PostgreSQL 17 + pgvector, volume nomeado) e `api` |
| `frontend/docker-compose.yml` | `web` |

Os dois se encontram pela rede externa `prescritiva-net`. O frontend é reconstruído ou
reiniciado sem tocar no banco, e o backend sobe sozinho para integração com sistemas da planta.

- Configuração centralizada em `app/config.py` via `pydantic-settings`, lida de `.env`.
- `.env.example` em cada app, documentando todas as variáveis.
- `app/scripts/init_db.py`: cria extensão, schema e índices de forma idempotente.
- `app/scripts/gen_secrets.py`: gera os segredos de autenticação (SPEC-FEAT-016).
- `tasks.ps1` com os alvos: `up`, `down`, `init`, `ingest`, `api`, `test`.

## Fora de escopo

- Orquestração em Kubernetes (fica descrita no documento de arquitetura, não implementada).
- Cadastro e gestão de usuários finais — a autenticação é máquina-a-máquina (SPEC-FEAT-016).

## Decisões técnicas

- **Um banco só (PostgreSQL + pgvector) em vez de banco vetorial dedicado.** O volume é de
  ~167 mil vetores de 18 dimensões e algumas centenas de chunks de documento; não justifica
  um segundo serviço, e permite fazer o `JOIN` entre similaridade de sensor e metadado de
  falha em uma única consulta SQL.
- **Compose por aplicação, não um só na raiz.** Backend e frontend têm ciclos de vida
  independentes: em planta, a API sobe junto do banco e a interface é implantada à parte.
  Um compose único acoplaria os dois e obrigaria a derrubar o banco para publicar a interface.
- **Sem migrations (Alembic) nesta entrega.** O schema é criado por script versionado; a
  base é reconstruída por ingestão, não evoluída em produção.

## Contrato

```
DATABASE_URL=postgresql+psycopg://prescritiva:...@localhost:5433/prescritiva
LLM_PROVIDER=openai|deepseek
LLM_API_KEY=...
LLM_MODEL=...
LLM_BASE_URL=...           # vazio para OpenAI
VISION_MODEL=...           # usado apenas no OCR (SPEC-FEAT-006)
EMBEDDING_MODEL=intfloat/multilingual-e5-small
JWT_SECRET= / API_CLIENT_ID= / API_CLIENT_SECRET=    # externo  (SPEC-FEAT-016)
INTERNAL_API_KEY=                                    # interno  (SPEC-FEAT-016)
```
