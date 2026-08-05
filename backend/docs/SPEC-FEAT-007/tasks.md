# SPEC-FEAT-007 — Tarefas

**Feature:** Indexação semântica dos documentos

- [x] Definir schema de `documents` e `document_chunks`
- [x] Implementar `app/docs/chunking.py` com detecção de seções numeradas + fallback por tamanho
- [x] Implementar `app/rag/embeddings.py` encapsulando o `fastembed`
- [x] Implementar `app/scripts/ingest_docs.py` (extrai → chunka → embeda → grava)
- [x] Criar índice HNSW e tabela de metadados do índice
- [x] Testar recuperação com 5 consultas-sonda, uma por documento conhecido
- [x] Medir e registrar o tempo de indexação em CPU

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
