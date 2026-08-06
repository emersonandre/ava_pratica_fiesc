# SPEC-FEAT-011 — Tarefas

**Feature:** Geração prescritiva com citações

- [x] Escrever o prompt de sistema em português, com regra de abstenção
- [x] Implementar `app/rag/generator.py` com saída estruturada e validação por schema
- [x] Montar `evidencia` a partir do resultado de similaridade (código, não LLM)
- [x] Implementar retentativa em caso de saída fora do schema
- [x] Implementar extração e deduplicação da lista de citações
- [x] Avaliar 20 casos variados e registrar os resultados em `backend/docs/analise/geracao.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
