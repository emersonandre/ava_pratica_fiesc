# SPEC-FEAT-002 — Critérios de aceite

**Feature:** Taxonomia canônica de falhas  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Cobertura total dos rótulos**
  - *Verificação:* Os 151 rótulos distintos do `banner.csv` são mapeados; nenhum cai em `unknown`.

- [x] **Estados não são tratados como falha**
  - *Verificação:* `normal`, `normal_2`, `baseline`, `new_baseline`, `teste`, `new_teste`, `acelerando`, `motor_desligado`, `mortor_desligado_novo` retornam `is_problem = False`.

- [x] **Typos convergem para o canônico correto**
  - *Verificação:* `desabalanceado_3`, `desbanlanceado_carga_3_2`, `ddesbalanceado_adxl_0`, `dedesbalanceado_adxl_1` e `new_desabanceado_1` retornam família `desbalanceamento`.

- [x] **Sufixos de sessão não criam famílias novas**
  - *Verificação:* `rolamento_inner`, `rolamento_inner_2`, `rolamento_inner_carga`, `rolamento_inner_adxl_0` e `new_rolamento_inner_0` compartilham a mesma família `rolamento`.

- [x] **Famílias distintas não se fundem**
  - *Verificação:* `desalinhado` e `desbalanceado` produzem famílias diferentes.

- [x] **Rótulo desconhecido é erro, não silêncio**
  - *Verificação:* `normalize_fault('xpto_999')` levanta `UnknownFaultLabel`.

- [x] **Relatório auditável publicado**
  - *Verificação:* `backend/docs/analise/taxonomia.md` traz a matriz rótulo bruto → canônico → família, com contagem de registros por linha.
