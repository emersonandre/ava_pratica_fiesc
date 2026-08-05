# SPEC-FEAT-013 — API REST

| | |
| --- | --- |
| **App** | backend |
| **Épico** | API, seguranca e qualidade |
| **Atende** | DIF — APIs |
| **Depende de** | `SPEC-FEAT-005`, `SPEC-FEAT-012` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

A API tem **duas superfícies com públicos e riscos diferentes**, e por isso contratos e
autenticação diferentes (o mecanismo de cada uma está na SPEC-FEAT-016):

**Externa (`/api/v1/*`)** — consumida por sistemas da planta: CMMS, supervisório, coletor de
dados. Contrato mínimo, estável e versionado. Protegida por JWT `Bearer`. São só dois
endpoints de negócio, porque é tudo que um integrador precisa.

**Interna (`/api/internal/*`)** — consumida apenas pelo frontend, dentro da rede. Contrato
mais rico e sujeito a mudar junto com a interface. Protegida por chave estática.

## Escopo

### Superfície externa — `/api/v1` (JWT no cabeçalho `Authorization`)

| Método | Rota | Escopo | Função |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/token` | — | Troca `client_id`/`client_secret` por um JWT |
| `POST` | `/api/v1/predict` | `predict` | Recebe o JSON de métricas do sensor, roda o motor de similaridade, busca os documentos no banco vetorial, chama o LLM e devolve um JSON consolidado |
| `POST` | `/api/v1/upload_doc` | `upload` | Envia novo documento orientativo (PDF/texto), processa e injeta no banco vetorial |

O payload de `/api/v1/predict` aceita exatamente o JSON de exemplo do §2 do desafio.

### Superfície interna — `/api/internal` (cabeçalho `X-Internal-Key`)

| Método | Rota | Função |
| --- | --- | --- |
| `POST` | `/api/internal/events/similar` | Somente similaridade, sem LLM |
| `POST` | `/api/internal/chat` | Chat prescritivo com histórico e citações |
| `GET` | `/api/internal/stats/overview` | KPIs do dashboard |
| `GET` | `/api/internal/stats/timeline` | Distribuição temporal por família |
| `GET` | `/api/internal/faults` | Famílias canônicas e status de cobertura |
| `GET` | `/api/internal/documents` | Documentos indexados e estado da indexação |
| `GET` | `/api/internal/events/sample` | Amostra do holdout `new_*` para demonstração |

### Pública

| Método | Rota | Função |
| --- | --- | --- |
| `GET` | `/api/health` | Estado de banco, índice e provider |

## Fora de escopo

- Cadastro de usuários finais — a autenticação é máquina-a-máquina.
- Limite de requisições por cliente (rate limiting) — citado na arquitetura como próximo passo.

## Decisões técnicas

- **Superfície externa enxuta: `/predict` e `/upload_doc`.** Um integrador industrial precisa
  de duas operações — perguntar sobre um evento e ensinar um documento novo. Expor as dez
  rotas internas ao mundo criaria compromisso de compatibilidade sobre coisas que existem
  só para a interface.
- **`/api/v1` versionado só na superfície externa.** O contrato externo tem cliente de
  terceiro e não pode quebrar; o interno muda junto com o frontend, no mesmo repositório.
- **`/events/similar` separado do `/predict`.** Permite demonstrar a camada de dados sem
  custo nem latência de LLM, e deixa evidente na entrevista o que é estatística e o que é geração.
- **Tempo por etapa em toda resposta.** Similaridade, recuperação, geração e verificação —
  transparência e material de discussão sobre desempenho.

## Contrato

```http
POST /api/v1/auth/token
{ "client_id": "...", "client_secret": "..." }
200 → { "access_token": "...", "token_type": "bearer", "expires_in": 3600, "scopes": [...] }

POST /api/v1/predict
Authorization: Bearer <token>
{ "id": 114387, "created_at": "...", "z_rms_velocity_mm_s": 1.517, ..., "rpm": 1000.0 }
200 → { diagnosis, evidence, coverage, prescription | refusal, grounding, timings }

POST /api/v1/upload_doc      (multipart: file, fault_family, title)
Authorization: Bearer <token>
201 → { document_id, status, chunks, pages, method, coverage_updated }

POST /api/internal/chat
X-Internal-Key: <chave>
```
