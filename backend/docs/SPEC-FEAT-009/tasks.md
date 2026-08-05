# SPEC-FEAT-009 — Tarefas

**Feature:** Provider de LLM plugável

- [ ] Implementar `app/llm/provider.py` com o protocolo e a implementação OpenAI-compatível
- [ ] Adicionar resolução por `.env` e declaração de capacidades (visão)
- [ ] Adicionar timeout, retry com `tenacity` e teto de tokens
- [ ] Implementar log estruturado de uso (tokens, latência, custo estimado)
- [ ] Mapear exceções do SDK para erros de negócio da API
- [ ] Testar com provider inválido e confirmar degradação controlada

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
