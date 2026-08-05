# SPEC-FEAT-003 — Critérios de aceite

**Feature:** Feature engineering dos sinais de vibração  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Redundância comprovada, não presumida**
  - *Verificação:* Relatório mostra correlação ≈ 1,0 e razão constante (≈25,4) entre cada par `in_s`/`mm_s`, e a relação linear entre `temperature_f` e `temperature_c`.

- [x] **Vetor final sem duplicidade de grandeza**
  - *Verificação:* `FEATURE_COLUMNS` não contém nenhuma coluna `_in_s` nem `temperature_f`.

- [x] **Ordem das features é estável**
  - *Verificação:* `to_vector` produz o mesmo layout de `build_feature_frame`; teste compara índice a índice.

- [x] **Scaler é reutilizado, não reajustado**
  - *Verificação:* A inferência carrega `artifacts/scaler.joblib`; alterar o dado de entrada não altera média/desvio salvos.

- [x] **Motor desligado não contamina a escala**
  - *Verificação:* A média de RPM do scaler ajustado é calculada sem os registros `motor_desligado`.

- [x] **Sem NaN no vetor final**
  - *Verificação:* A ingestão do dataset completo produz zero valores nulos no vetor; qualquer nulo é reportado com o `id` do registro.
