# SPEC-FEAT-013 — Tarefas

**Feature:** API REST

- [x] Definir os schemas Pydantic de request e response em `app/schemas.py`
- [x] Implementar o roteador externo `app/api/v1/` (`auth`, `predict`, `upload_doc`)
- [x] Implementar o roteador interno `app/api/internal/` (events, chat, stats, documents)
- [x] Implementar middleware de tempo por etapa e log estruturado por requisição
- [x] Implementar tratamento de exceções de negócio
- [x] Configurar CORS a partir do `.env`
- [x] Implementar `/api/health` com verificação real de banco, índice e provider
- [x] Criar coleção de exemplos (`.http`) com uma chamada por rota, incluindo o fluxo de token

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
