# SPEC-FEAT-011 — Tarefas

**Feature:** Geração prescritiva com citações

- [ ] Escrever o prompt de sistema em português, com regra de abstenção
- [ ] Implementar `app/rag/generator.py` com saída estruturada e validação por schema
- [ ] Montar `evidencia` a partir do resultado de similaridade (código, não LLM)
- [ ] Implementar retentativa em caso de saída fora do schema
- [ ] Implementar extração e deduplicação da lista de citações
- [ ] Avaliar 20 casos variados e registrar os resultados em `backend/docs/analise/geracao.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
