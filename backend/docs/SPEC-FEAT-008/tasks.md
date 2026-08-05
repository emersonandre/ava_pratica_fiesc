# SPEC-FEAT-008 — Tarefas

**Feature:** Mapa falha→documento e gate de cobertura

- [x] Confirmar a falha-alvo do Doc1 após o OCR e fechar a tabela de cobertura
- [x] Definir schema de `fault_document_coverage`
- [x] Implementar consultas-sonda por família e registrar a evidência de cada vínculo
- [x] Implementar `app/rag/coverage.py` com `check_coverage` e os quatro motivos de retorno
- [x] Integrar o gate ao fluxo de análise, antes do retriever e do LLM
- [x] Escrever `tests/test_coverage.py` cobrindo os quatro motivos
- [x] Gerar `backend/docs/analise/cobertura.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
