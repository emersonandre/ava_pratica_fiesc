# SPEC-FEAT-017 — Tarefas

**Feature:** Ingestão de leituras do chão de fábrica

- [x] Tornar `canonical_fault`, `fault_family` e `is_problem` nulos no modelo
- [x] Adicionar o valor `producao` à restrição de `split`
- [x] Reescrever o índice HNSW parcial para `split <> 'holdout' AND fault_family IS NOT NULL`
- [x] Ajustar as consultas do repositório ao novo critério de histórico
- [x] Implementar `excluir_id` em `buscar_vizinhos`, `similarity` e `pipeline`
- [x] Implementar `schemas/ingest.py` com o payload do enunciado
- [x] Implementar `services/ingestion.py` com upsert e tolerância a rótulo desconhecido
- [x] Implementar `POST /api/v1/events` com o escopo `ingest`
- [x] Adicionar o escopo `ingest` à emissão de token
- [x] Escrever os testes de aceite em `tests/test_api.py`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
