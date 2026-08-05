# SPEC-FEAT-016 — Tarefas

**Feature:** Autenticação: JWT externo e chave interna

- [x] Implementar `app/security.py` (emissão, verificação, escopos, chave interna)
- [x] Adicionar as variáveis de autenticação ao `config.py` e aos dois `.env.example`
- [x] Implementar `app/scripts/gen_secrets.py`
- [x] Implementar `POST /api/v1/auth/token` com comparação em tempo constante
- [x] Aplicar `require_scope` nos endpoints externos e `require_internal_key` nos internos
- [x] Implementar `require_auth()` na inicialização da aplicação
- [x] Configurar o proxy do frontend para injetar `X-Internal-Key` sem expô-la ao navegador
- [x] Escrever `tests/test_security.py` cobrindo cada critério de aceite

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
