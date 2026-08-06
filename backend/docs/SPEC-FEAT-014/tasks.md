# SPEC-FEAT-014 — Tarefas

**Feature:** Registro de novo documento de falha

- [x] Implementar a rota de upload com validação de tipo e tamanho
- [x] Reaproveitar o pipeline de extração/chunking/embedding para um documento avulso
- [x] Implementar deduplicação por hash de conteúdo
- [x] Implementar máquina de estados de indexação e persistência do erro
- [x] Implementar recálculo de cobertura e invalidação de cache
- [x] Testar o ciclo recusa → upload → resposta ponta a ponta
- [x] Registrar o roteiro dessa demonstração em `backend/docs/analise/demo.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
