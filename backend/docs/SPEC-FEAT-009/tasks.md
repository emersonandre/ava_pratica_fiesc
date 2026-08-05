# SPEC-FEAT-009 — Tarefas

**Feature:** Provider de LLM plugável

- [x] Implementar `app/llm/provider.py` com o protocolo e a implementação OpenAI-compatível
- [x] Adicionar resolução por `.env` e declaração de capacidades (visão)
- [x] Adicionar timeout, retry com `tenacity` e teto de tokens
- [x] Implementar log estruturado de uso (tokens, latência, custo estimado)
- [x] Mapear exceções do SDK para erros de negócio da API
- [x] Testar com provider inválido e confirmar degradação controlada

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
