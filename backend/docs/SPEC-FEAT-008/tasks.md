# SPEC-FEAT-008 — Tarefas

**Feature:** Mapa falha→documento e gate de cobertura

- [ ] Confirmar a falha-alvo do Doc1 após o OCR e fechar a tabela de cobertura
- [ ] Definir schema de `fault_document_coverage`
- [ ] Implementar consultas-sonda por família e registrar a evidência de cada vínculo
- [ ] Implementar `app/rag/coverage.py` com `check_coverage` e os quatro motivos de retorno
- [ ] Integrar o gate ao fluxo de análise, antes do retriever e do LLM
- [ ] Escrever `tests/test_coverage.py` cobrindo os quatro motivos
- [ ] Gerar `backend/docs/analise/cobertura.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
