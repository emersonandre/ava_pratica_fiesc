# SPEC-FEAT-003 — Tarefas

**Feature:** Feature engineering dos sinais de vibração

- [ ] Script de auditoria: correlação e razão entre pares de unidade, salvo em `backend/docs/analise/features.md`
- [x] Implementar `app/core/features.py` com `FEATURE_COLUMNS` e `build_feature_frame`
- [x] Implementar ajuste e persistência do `StandardScaler` excluindo `motor_desligado`
- [x] Implementar `to_vector` para o payload de inferência (JSON do §2 do desafio)
- [x] Escrever `tests/test_features.py` (ordem estável, ausência de NaN, reuso do scaler)
- [ ] Documentar em `backend/docs/analise/features.md` cada coluna descartada e o porquê

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
