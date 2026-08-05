# SPEC-FEAT-013 — Tarefas

**Feature:** API REST

- [ ] Definir os schemas Pydantic de request e response em `app/schemas.py`
- [ ] Implementar o roteador externo `app/api/v1/` (`auth`, `predict`, `upload_doc`)
- [ ] Implementar o roteador interno `app/api/internal/` (events, chat, stats, documents)
- [ ] Implementar middleware de tempo por etapa e log estruturado por requisição
- [ ] Implementar tratamento de exceções de negócio
- [ ] Configurar CORS a partir do `.env`
- [ ] Implementar `/api/health` com verificação real de banco, índice e provider
- [ ] Criar coleção de exemplos (`.http`) com uma chamada por rota, incluindo o fluxo de token

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
