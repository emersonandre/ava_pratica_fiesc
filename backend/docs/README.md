# Backend — Manutenção Prescritiva — Specs

**Stack:** Python 3.13 · FastAPI · PostgreSQL 17 + pgvector · fastembed (ONNX) · OpenAI/DeepSeek

Gerado por `tools/specs/gen.py` a partir de `tools/specs/catalog_backend.py`. Não edite este arquivo à mão — marque os checkboxes em `tasks.md` / `acceptance.md` e rode o gerador de novo.

⬜ Pendente · 🟨 Em andamento · ✅ Concluído · ⛔ Descartado

## Resumo

| | |
| --- | --- |
| Features | 17 |
| Features concluídas | 13 |
| Tarefas concluídas | 117 / 122 (96%) |

## Infraestrutura e dados

| Status | Feature | Tarefas | Aceite |
| :---: | --- | :---: | :---: |
| 🟨 | [SPEC-FEAT-001 — Infraestrutura local reproduzível](SPEC-FEAT-001/spec.md) | 10/11 | 6/6 |
| ✅ | [SPEC-FEAT-002 — Taxonomia canônica de falhas](SPEC-FEAT-002/spec.md) | 7/7 | 7/7 |
| ✅ | [SPEC-FEAT-003 — Feature engineering dos sinais de vibração](SPEC-FEAT-003/spec.md) | 6/6 | 6/6 |
| 🟨 | [SPEC-FEAT-004 — Ingestão do banner.csv com split temporal](SPEC-FEAT-004/spec.md) | 6/7 | 7/7 |

## Similaridade e documentos

| Status | Feature | Tarefas | Aceite |
| :---: | --- | :---: | :---: |
| ✅ | [SPEC-FEAT-005 — Motor de similaridade histórica](SPEC-FEAT-005/spec.md) | 7/7 | 6/6 |
| ✅ | [SPEC-FEAT-006 — Extração de texto e OCR dos documentos](SPEC-FEAT-006/spec.md) | 7/7 | 6/6 |
| ✅ | [SPEC-FEAT-007 — Indexação semântica dos documentos](SPEC-FEAT-007/spec.md) | 7/7 | 6/6 |
| ✅ | [SPEC-FEAT-008 — Mapa falha→documento e gate de cobertura](SPEC-FEAT-008/spec.md) | 7/7 | 7/7 |

## RAG e LLM

| Status | Feature | Tarefas | Aceite |
| :---: | --- | :---: | :---: |
| 🟨 | [SPEC-FEAT-009 — Provider de LLM plugável](SPEC-FEAT-009/spec.md) | 6/6 | 4/5 |
| ✅ | [SPEC-FEAT-010 — Recuperação de contexto para prescrição](SPEC-FEAT-010/spec.md) | 6/6 | 5/5 |
| ✅ | [SPEC-FEAT-011 — Geração prescritiva com citações](SPEC-FEAT-011/spec.md) | 6/6 | 6/6 |
| ✅ | [SPEC-FEAT-012 — Guarda anti-alucinação](SPEC-FEAT-012/spec.md) | 6/6 | 7/7 |

## API, seguranca e qualidade

| Status | Feature | Tarefas | Aceite |
| :---: | --- | :---: | :---: |
| ✅ | [SPEC-FEAT-013 — API REST](SPEC-FEAT-013/spec.md) | 8/8 | 9/9 |
| ✅ | [SPEC-FEAT-014 — Registro de novo documento de falha](SPEC-FEAT-014/spec.md) | 7/7 | 6/6 |
| ✅ | [SPEC-FEAT-017 — Ingestão de leituras do chão de fábrica](SPEC-FEAT-017/spec.md) | 10/10 | 9/9 |
| ✅ | [SPEC-FEAT-016 — Autenticação: JWT externo e chave interna](SPEC-FEAT-016/spec.md) | 8/8 | 9/9 |
| 🟨 | [SPEC-FEAT-015 — Testes, qualidade e observabilidade](SPEC-FEAT-015/spec.md) | 3/6 | 5/6 |
