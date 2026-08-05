# SPEC-FEAT-012 — Tarefas

**Feature:** Guarda anti-alucinação

- [ ] Escrever a suíte adversarial `tests/test_alucinacao.py` (coberta, descoberta, fora de domínio, premissa falsa)
- [ ] Implementar `app/rag/grounding.py` com decomposição em afirmações e verificação
- [ ] Definir a política de remoção × marcação por tipo de campo
- [ ] Integrar a verificação ao fluxo de geração e expor `GroundingReport` na API
- [ ] Rodar a suíte, registrar o score e publicar no README
- [ ] Documentar as limitações conhecidas em `backend/docs/analise/alucinacao.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
