# SPEC-FEAT-014 — Tarefas

**Feature:** Registro de novo documento de falha

- [ ] Implementar a rota de upload com validação de tipo e tamanho
- [ ] Reaproveitar o pipeline de extração/chunking/embedding para um documento avulso
- [ ] Implementar deduplicação por hash de conteúdo
- [ ] Implementar máquina de estados de indexação e persistência do erro
- [ ] Implementar recálculo de cobertura e invalidação de cache
- [ ] Testar o ciclo recusa → upload → resposta ponta a ponta
- [ ] Registrar o roteiro dessa demonstração em `backend/docs/analise/demo.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
