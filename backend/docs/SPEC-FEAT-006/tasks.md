# SPEC-FEAT-006 — Tarefas

**Feature:** Extração de texto e OCR dos documentos

- [x] Implementar `app/docs/extract.py` com detecção de camada de texto
- [x] Implementar caminho de texto com `pypdf` preservando número de página
- [x] Implementar renderização de páginas com `pypdfium2` em resolução adequada a OCR
- [x] Implementar OCR por modelo de visão, com cache em `artifacts/ocr/` por hash de página
- [x] Implementar normalização de texto (hifenização, cabeçalho/rodapé, espaços)
- [x] Rodar sobre os 6 PDFs e identificar a falha-alvo do Doc1
- [x] Gerar `backend/docs/analise/documentos.md` com um resumo por documento

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
