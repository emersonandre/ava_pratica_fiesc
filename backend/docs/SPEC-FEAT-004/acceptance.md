# SPEC-FEAT-004 — Critérios de aceite

**Feature:** Ingestão do banner.csv com split temporal  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Volume íntegro**
  - *Verificação:* `SELECT count(*) FROM sensor_events` retorna 166.796 e a contagem por família bate com o relatório de EDA.

- [x] **Split sem vazamento temporal**
  - *Verificação:* `MAX(created_at)` do split `train` é anterior ao `MIN(created_at)` do split `holdout`.

- [x] **Holdout corresponde aos rótulos `new_*`**
  - *Verificação:* Todo registro com `split='holdout'` tem `raw_fault` começando com `new_`, e vice-versa.

- [x] **Reexecução é idempotente**
  - *Verificação:* Rodar a ingestão duas vezes mantém a contagem em 166.796.

- [x] **Busca vetorial é rápida**
  - *Verificação:* KNN (k=50) sobre os 166k vetores responde em menos de 100 ms com o índice HNSW ativo.

- [x] **Busca filtrada retorna resultado**
  - *Verificação:* KNN partindo de um evento do holdout, filtrado por `split='train'`, retorna k vizinhos — nunca lista vazia (regressão do pós-filtro do HNSW).

- [ ] **Falha de rótulo interrompe a carga**
  - *Verificação:* Um rótulo fora da taxonomia aborta a ingestão com mensagem citando o `id` e o valor bruto.
