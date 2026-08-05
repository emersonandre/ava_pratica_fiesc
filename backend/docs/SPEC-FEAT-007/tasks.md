# SPEC-FEAT-007 — Tarefas

**Feature:** Indexação semântica dos documentos

- [ ] Definir schema de `documents` e `document_chunks`
- [ ] Implementar `app/docs/chunking.py` com detecção de seções numeradas + fallback por tamanho
- [ ] Implementar `app/rag/embeddings.py` encapsulando o `fastembed`
- [ ] Implementar `app/scripts/ingest_docs.py` (extrai → chunka → embeda → grava)
- [ ] Criar índice HNSW e tabela de metadados do índice
- [ ] Testar recuperação com 5 consultas-sonda, uma por documento conhecido
- [ ] Medir e registrar o tempo de indexação em CPU

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
