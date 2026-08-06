# SPEC-FEAT-005 — Tarefas

**Feature:** Motor de similaridade histórica

- [x] Implementar `app/ml/similarity.py`: consulta KNN parametrizada por `k`
- [x] Implementar voto ponderado e cálculo de confiança
- [x] Calibrar o limiar de fora de distribuição a partir das distâncias intra-família
- [x] Implementar as agregações (contagem, timeline, frequência, MTBF, contexto operacional)
- [x] Script de avaliação sobre o holdout, gerando a matriz de confusão por família
- [x] Escrever `tests/test_similarity.py` (vazamento, fora de distribuição, confiança)
- [x] Documentar resultados e limitações em `backend/docs/analise/similaridade.md`

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
