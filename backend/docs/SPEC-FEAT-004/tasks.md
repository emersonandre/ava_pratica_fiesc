# SPEC-FEAT-004 — Tarefas

**Feature:** Ingestão do banner.csv com split temporal

- [x] Definir o schema de `sensor_events` em `app/models.py`
- [x] Implementar `app/scripts/ingest_csv.py` com leitura em chunks e barra de progresso
- [x] Aplicar taxonomia e features; abortar em rótulo desconhecido
- [x] Implementar a regra de split e validá-la contra as datas reais
- [x] Criar o índice HNSW e medir a latência de KNN antes/depois
- [ ] Implementar upsert por `id` e testar a reexecução
- [ ] Gerar `backend/docs/analise/dataset.md` com contagens, período e distribuição por família

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
