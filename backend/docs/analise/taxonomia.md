# Taxonomia canonica de falhas

> Gerado por `python manage.py report_taxonomy` a partir de `dados/banner.csv`.
> Evidencia da [SPEC-FEAT-002](../SPEC-FEAT-002/spec.md).

## Resumo

| | |
| --- | --- |
| Registros | 166.796 |
| Rotulos brutos distintos | 151 |
| Rotulos canonicos | 18 |
| Familias | 14 |
| Familias de problema | 9 |
| Registros classificados como problema | 151.064 (90.6%) |
| Rotulos sem regra | 0 |

## Familias

| Familia | Descricao | Problema | Registros | % |
| --- | --- | :---: | ---: | ---: |
| `rolamento` | Defeito em rolamento (pista interna. externa. esferas ou combinado) | sim | 60.779 | 36.4% |
| `eccentric_rotor` | Centro geometrico do rotor deslocado do centro de rotacao | sim | 16.497 | 9.9% |
| `normal` | Operacao normal | nao | 15.058 | 9.0% |
| `cocked_rotor` | Rotor inclinado em relacao ao eixo de rotacao | sim | 14.275 | 8.6% |
| `desbalanceamento` | Distribuicao desigual de massa no rotor | sim | 13.237 | 7.9% |
| `ventoinha` | Defeito na ventoinha do motor | sim | 12.299 | 7.4% |
| `polia` | Defeito em polia (excentricidade. desbalanceamento. desgaste) | sim | 12.000 | 7.2% |
| `correia` | Defeito no sistema de transmissao por correia | sim | 11.999 | 7.2% |
| `desalinhamento` | Eixos do motor e da carga fora de alinhamento | sim | 9.178 | 5.5% |
| `falta_fase` | Operacao com falta de fase na alimentacao eletrica | sim | 800 | 0.5% |
| `motor_desligado` | Motor parado | nao | 497 | 0.3% |
| `teste` | Coleta de teste | nao | 101 | 0.1% |
| `baseline` | Coleta de referencia | nao | 69 | 0.0% |
| `acelerando` | Transiente de aceleracao | nao | 7 | 0.0% |

## Erros de digitacao corrigidos

Correcoes aplicadas no nivel do token, todas confirmadas no dataset.

| Token errado | Token correto |
| --- | --- |
| `cockecocked` | `cocked` |
| `comb` | `combination` |
| `ddesbalanceado` | `desbalanceado` |
| `dedesbalanceado` | `desbalanceado` |
| `desabalanceado` | `desbalanceado` |
| `desabanceado` | `desbalanceado` |
| `desbalanceamento` | `desbalanceado` |
| `desbanlanceado` | `desbalanceado` |
| `mortor` | `motor` |
| `normla` | `normal` |

## Matriz completa: rotulo bruto -> canonico

Os 151 rotulos brutos do dataset, agrupados por familia.

| Rotulo bruto | Canonico | Familia | Problema | Registros | Periodo |
| --- | --- | --- | :---: | ---: | --- |
| `acelerando` | `acelerando` | `acelerando` | nao | 7 | 2026-05-21 |
| `new_baseline` | `baseline` | `baseline` | nao | 69 | 2026-06-11 |
| `cocked_rotor` | `cocked_rotor` | `cocked_rotor` | sim | 10.000 | 2026-05-18 a 2026-06-01 |
| `cocked_rotor_2` | `cocked_rotor` | `cocked_rotor` | sim | 3.075 | 2026-06-01 |
| `cocked_rotor_pos_2` | `cocked_rotor` | `cocked_rotor` | sim | 150 | 2026-06-05 |
| `cocked_rotor_2_pos_2` | `cocked_rotor` | `cocked_rotor` | sim | 150 | 2026-06-05 |
| `cocked_rotor_carga` | `cocked_rotor` | `cocked_rotor` | sim | 150 | 2026-06-05 |
| `new_cocked_0` | `cocked_rotor` | `cocked_rotor` | sim | 150 | 2026-06-10 |
| `new_cocked_1` | `cocked_rotor` | `cocked_rotor` | sim | 150 | 2026-06-10 a 2026-06-11 |
| `new_cocked_2` | `cocked_rotor` | `cocked_rotor` | sim | 150 | 2026-06-11 |
| `new_cocked_3` | `cocked_rotor` | `cocked_rotor` | sim | 150 | 2026-06-11 |
| `cocked_adxl_0` | `cocked_rotor` | `cocked_rotor` | sim | 100 | 2026-06-09 |
| `cockecocked_adxl_0` | `cocked_rotor` | `cocked_rotor` | sim | 50 | 2026-06-09 |
| `correia` | `correia` | `correia` | sim | 9.000 | 2026-05-27 a 2026-06-01 |
| `correia_2` | `correia` | `correia` | sim | 2.999 | 2026-06-03 |
| `desalinhado` | `desalinhamento` | `desalinhamento` | sim | 4.000 | 2026-06-03 a 2026-06-05 |
| `desalinhado_2` | `desalinhamento` | `desalinhamento` | sim | 3.998 | 2026-06-04 a 2026-06-05 |
| `new_desalinhado_2` | `desalinhamento` | `desalinhamento` | sim | 400 | 2026-06-12 a 2026-06-16 |
| `new_desalinhado_1` | `desalinhamento` | `desalinhamento` | sim | 200 | 2026-06-12 a 2026-06-15 |
| `new_desalinhado_3` | `desalinhamento` | `desalinhamento` | sim | 200 | 2026-06-16 |
| `new_desalinhado_0` | `desalinhamento` | `desalinhamento` | sim | 199 | 2026-06-16 |
| `desalinhado_3` | `desalinhamento` | `desalinhamento` | sim | 150 | 2026-06-05 |
| `new_desalinhado_4` | `desalinhamento` | `desalinhamento` | sim | 31 | 2026-06-16 |
| `new_desbalanceado_2` | `desbalanceamento` | `desbalanceamento` | sim | 208 | 2026-06-16 |
| `new_desbalanceado_0` | `desbalanceamento` | `desbalanceamento` | sim | 200 | 2026-06-15 |
| `new_desbalanceado_1` | `desbalanceamento` | `desbalanceamento` | sim | 200 | 2026-06-15 |
| `new_desbalanceado_3` | `desbalanceamento` | `desbalanceamento` | sim | 200 | 2026-06-16 |
| `desbalanceado_pos_2` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-05 |
| `desbalanceado_2_pos_2` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-05 |
| `desbalanceado_carga` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-05 |
| `desbalanceado_carga_2` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-05 |
| `desbalanceado_novo` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-05 |
| `new_desbalanceado_antigo_1` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-10 |
| `new_desbalanceado_antigo_3` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-11 |
| `new_desbalanceado_antigo_0` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-10 |
| `new_desbalanceado_antigo_2` | `desbalanceamento` | `desbalanceamento` | sim | 150 | 2026-06-11 |
| `desbalanceado_3` | `desbalanceamento` | `desbalanceamento` | sim | 100 | 2026-06-05 |
| `desbalanceado_carga_3` | `desbalanceamento` | `desbalanceamento` | sim | 100 | 2026-06-06 |
| `desbalanceado_carga_3_2` | `desbalanceamento` | `desbalanceamento` | sim | 100 | 2026-06-06 |
| `desbalanceamento` | `desbalanceamento` | `desbalanceamento` | sim | 100 | 2026-06-09 |
| `desbalanceado_adxl_0` | `desbalanceamento` | `desbalanceamento` | sim | 100 | 2026-06-09 |
| `desabalanceado_3` | `desbalanceamento` | `desbalanceamento` | sim | 50 | 2026-06-05 |
| `desbanlanceado_carga_3_2` | `desbalanceamento` | `desbalanceamento` | sim | 50 | 2026-06-06 |
| `ddesbalanceado_adxl_0` | `desbalanceamento` | `desbalanceamento` | sim | 50 | 2026-06-09 |
| `new_desabanceado_1` | `desbalanceamento` | `desbalanceamento` | sim | 50 | 2026-06-15 |
| `desbalanceado_adxl_1` | `desbalanceamento` | `desbalanceamento` | sim | 42 | 2026-06-09 |
| `dedesbalanceado_adxl_1` | `desbalanceamento` | `desbalanceamento` | sim | 21 | 2026-06-09 |
| `desbalanceado_1parafuso` | `desbalanceamento_1parafuso` | `desbalanceamento` | sim | 10.079 | 2026-04-30 a 2026-06-02 |
| `desbalanceado_1parafuso_3` | `desbalanceamento_1parafuso` | `desbalanceamento` | sim | 237 | 2026-06-04 |
| `eccentric_rotor` | `eccentric_rotor` | `eccentric_rotor` | sim | 11.808 | 2026-05-12 a 2026-05-18 |
| `eccentric_rotor_2` | `eccentric_rotor` | `eccentric_rotor` | sim | 3.000 | 2026-06-01 a 2026-06-02 |
| `eccentric_rotor_3` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-05 |
| `eccentric_rotor_4` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-05 |
| `eccentric_rotor_pos_2` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-05 |
| `eccentric_rotor_2_pos_2` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-05 |
| `eccentric_rotor_carga` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-05 |
| `eccentric_rotor_carga_2` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-05 |
| `eccentric_adxl_0` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-09 |
| `new_eccentric_0` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-10 |
| `new_eccentric_1` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-11 |
| `new_eccentric_2` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-11 |
| `new_eccentric_3` | `eccentric_rotor` | `eccentric_rotor` | sim | 150 | 2026-06-11 |
| `eccentric_2_pos_2` | `eccentric_rotor` | `eccentric_rotor` | sim | 39 | 2026-06-05 |
| `new_falta_fase_0` | `falta_fase` | `falta_fase` | sim | 200 | 2026-06-12 a 2026-06-16 |
| `new_falta_fase_1` | `falta_fase` | `falta_fase` | sim | 200 | 2026-06-16 |
| `new_falta_fase_2` | `falta_fase` | `falta_fase` | sim | 200 | 2026-06-16 |
| `new_falta_fase_3` | `falta_fase` | `falta_fase` | sim | 200 | 2026-06-16 |
| `motor_desligado` | `motor_desligado` | `motor_desligado` | nao | 397 | 2026-04-30 a 2026-06-05 |
| `motor_desligado_novo` | `motor_desligado` | `motor_desligado` | nao | 50 | 2026-06-05 |
| `mortor_desligado_novo` | `motor_desligado` | `motor_desligado` | nao | 50 | 2026-06-05 |
| `normal_2` | `normal` | `normal` | nao | 6.000 | 2026-06-03 a 2026-06-05 |
| `normal` | `normal` | `normal` | nao | 5.738 | 2026-04-30 a 2026-06-09 |
| `normal_carga` | `normal` | `normal` | nao | 300 | 2026-06-05 |
| `normal_novo` | `normal` | `normal` | nao | 300 | 2026-06-05 |
| `new_normal_0` | `normal` | `normal` | nao | 200 | 2026-06-10 a 2026-06-15 |
| `new_normal_1` | `normal` | `normal` | nao | 200 | 2026-06-10 a 2026-06-16 |
| `new_normal_2` | `normal` | `normal` | nao | 200 | 2026-06-11 a 2026-06-16 |
| `new_normal_3` | `normal` | `normal` | nao | 200 | 2026-06-11 a 2026-06-16 |
| `new_normal_6` | `normal` | `normal` | nao | 200 | 2026-06-12 |
| `normal_pos_2` | `normal` | `normal` | nao | 150 | 2026-06-05 |
| `normal_2_pos_2` | `normal` | `normal` | nao | 150 | 2026-06-05 |
| `normal_3_pos_2` | `normal` | `normal` | nao | 150 | 2026-06-05 |
| `normal_carga_3` | `normal` | `normal` | nao | 150 | 2026-06-06 |
| `normal_carga_3_2` | `normal` | `normal` | nao | 150 | 2026-06-06 |
| `normal_adxl_0` | `normal` | `normal` | nao | 150 | 2026-06-09 |
| `normal_adxl_1` | `normal` | `normal` | nao | 150 | 2026-06-09 |
| `new_normal_4` | `normal` | `normal` | nao | 150 | 2026-06-12 |
| `new_normal_5` | `normal` | `normal` | nao | 150 | 2026-06-12 |
| `normal_3` | `normal` | `normal` | nao | 100 | 2026-06-05 |
| `normal_novo_teste` | `normal` | `normal` | nao | 100 | 2026-06-05 |
| `normal_carga_3_3` | `normal` | `normal` | nao | 100 | 2026-06-06 |
| `normla_carga_3_3` | `normal` | `normal` | nao | 50 | 2026-06-06 |
| `normal_6` | `normal` | `normal` | nao | 20 | 2026-06-09 |
| `polia` | `polia` | `polia` | sim | 9.000 | 2026-05-25 a 2026-05-26 |
| `polia_2` | `polia` | `polia` | sim | 3.000 | 2026-06-02 |
| `rolamento_ball` | `rolamento_ball` | `rolamento` | sim | 9.004 | 2026-05-21 a 2026-05-25 |
| `rolamento_ball_2` | `rolamento_ball` | `rolamento` | sim | 3.000 | 2026-06-02 a 2026-06-03 |
| `new_rolamento_ball_0` | `rolamento_ball` | `rolamento` | sim | 200 | 2026-06-10 a 2026-06-15 |
| `new_rolamento_ball_1` | `rolamento_ball` | `rolamento` | sim | 200 | 2026-06-10 a 2026-06-16 |
| `new_rolamento_ball_2` | `rolamento_ball` | `rolamento` | sim | 200 | 2026-06-11 a 2026-06-16 |
| `new_rolamento_ball_3` | `rolamento_ball` | `rolamento` | sim | 200 | 2026-06-11 a 2026-06-16 |
| `rolamento_ball_3` | `rolamento_ball` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_ball_4` | `rolamento_ball` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_ball_pos_2` | `rolamento_ball` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_ball_carga` | `rolamento_ball` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_ball_carga_3` | `rolamento_ball` | `rolamento` | sim | 150 | 2026-06-06 |
| `rolamento_ball_adxl_0` | `rolamento_ball` | `rolamento` | sim | 150 | 2026-06-09 |
| `rolamento_combination` | `rolamento_combination` | `rolamento` | sim | 10.000 | 2026-05-22 a 2026-05-25 |
| `rolamento_combination_2` | `rolamento_combination` | `rolamento` | sim | 3.000 | 2026-06-03 |
| `new_rolamento_comb_0` | `rolamento_combination` | `rolamento` | sim | 200 | 2026-06-10 a 2026-06-15 |
| `new_rolamento_comb_1` | `rolamento_combination` | `rolamento` | sim | 200 | 2026-06-10 a 2026-06-16 |
| `new_rolamento_comb_2` | `rolamento_combination` | `rolamento` | sim | 200 | 2026-06-11 a 2026-06-16 |
| `new_rolamento_comb_3` | `rolamento_combination` | `rolamento` | sim | 200 | 2026-06-11 a 2026-06-16 |
| `rolamento_combination_3` | `rolamento_combination` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_combination_4` | `rolamento_combination` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_combination_pos_2` | `rolamento_combination` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_combination_carga` | `rolamento_combination` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_comb_adxl_0` | `rolamento_combination` | `rolamento` | sim | 150 | 2026-06-09 |
| `rolamento_inner` | `rolamento_inner` | `rolamento` | sim | 13.000 | 2026-05-20 a 2026-05-22 |
| `rolamento_inner_2` | `rolamento_inner` | `rolamento` | sim | 3.012 | 2026-06-02 |
| `new_rolamento_inner_0` | `rolamento_inner` | `rolamento` | sim | 200 | 2026-06-10 a 2026-06-15 |
| `new_rolamento_inner_1` | `rolamento_inner` | `rolamento` | sim | 200 | 2026-06-10 a 2026-06-16 |
| `new_rolamento_inner_2` | `rolamento_inner` | `rolamento` | sim | 200 | 2026-06-12 a 2026-06-16 |
| `new_rolamento_inner_3` | `rolamento_inner` | `rolamento` | sim | 200 | 2026-06-11 a 2026-06-16 |
| `rolamento_inner_3` | `rolamento_inner` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_inner_4` | `rolamento_inner` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_inner_pos_2` | `rolamento_inner` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_inner_carga` | `rolamento_inner` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_inner_carga_2` | `rolamento_inner` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_inner_adxl_0` | `rolamento_inner` | `rolamento` | sim | 150 | 2026-06-09 |
| `rolamento_outer` | `rolamento_outer` | `rolamento` | sim | 10.000 | 2026-05-19 a 2026-05-20 |
| `rolamento_outer_2` | `rolamento_outer` | `rolamento` | sim | 3.000 | 2026-06-02 a 2026-06-03 |
| `new_rolamento_outer_0` | `rolamento_outer` | `rolamento` | sim | 200 | 2026-06-10 a 2026-06-15 |
| `new_rolamento_outer_1` | `rolamento_outer` | `rolamento` | sim | 200 | 2026-06-10 a 2026-06-16 |
| `new_rolamento_outer_3` | `rolamento_outer` | `rolamento` | sim | 200 | 2026-06-11 a 2026-06-16 |
| `new_rolamento_outer_2` | `rolamento_outer` | `rolamento` | sim | 200 | 2026-06-12 a 2026-06-16 |
| `rolamento_outer_3` | `rolamento_outer` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_outer_4` | `rolamento_outer` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_outer_pos_2` | `rolamento_outer` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_outer_carga` | `rolamento_outer` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_outer_novo` | `rolamento_outer` | `rolamento` | sim | 150 | 2026-06-05 |
| `rolamento_outer_adxl_0` | `rolamento_outer` | `rolamento` | sim | 150 | 2026-06-09 |
| `rolamento_outer_adxl_1` | `rolamento_outer` | `rolamento` | sim | 63 | 2026-06-09 |
| `rolamento_outer_novo_teste` | `rolamento_outer` | `rolamento` | sim | 50 | 2026-06-05 |
| `teste` | `teste` | `teste` | nao | 97 | 2026-06-05 a 2026-06-09 |
| `new_tes` | `teste` | `teste` | nao | 2 | 2026-06-12 |
| `new_teste` | `teste` | `teste` | nao | 2 | 2026-06-12 |
| `ventoinha` | `ventoinha` | `ventoinha` | sim | 9.000 | 2026-05-26 a 2026-05-27 |
| `ventoinha_2` | `ventoinha` | `ventoinha` | sim | 2.999 | 2026-06-02 |
| `ventoinha_3` | `ventoinha` | `ventoinha` | sim | 150 | 2026-06-05 |
| `ventoinha_adxl_0` | `ventoinha` | `ventoinha` | sim | 150 | 2026-06-09 |
