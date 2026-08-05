# SPEC-FEAT-005 — Tarefas

**Feature:** Motor de similaridade histórica

- [ ] Implementar `app/ml/similarity.py`: consulta KNN parametrizada por `k`
- [ ] Implementar voto ponderado e cálculo de confiança
- [ ] Calibrar o limiar de fora de distribuição a partir das distâncias intra-família
- [ ] Implementar as agregações (contagem, timeline, frequência, MTBF, contexto operacional)
- [ ] Script de avaliação sobre o holdout, gerando a matriz de confusão por família
- [ ] Escrever `tests/test_similarity.py` (vazamento, fora de distribuição, confiança)
- [ ] Documentar resultados e limitações em `backend/docs/analise/similaridade.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
