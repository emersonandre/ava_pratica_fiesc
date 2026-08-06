# Conjunto de dados

> Gerado por `python manage.py report dataset`.
> Evidencia da [SPEC-FEAT-004](../SPEC-FEAT-004/spec.md).

## Volume

| | |
| --- | ---: |
| Leituras | 166.796 |
| Rotulos brutos distintos | 151 |
| Familias canonicas | 14 |
| Familias que representam problema | 9 |
| Leituras classificadas como problema | 151.064 (90.6%) |

## Corte temporal

Todo rotulo com prefixo `new_` foi coletado entre 10 e 16 de junho; todo o
restante e de ate 09 de junho. O conjunto de teste sai desse corte natural,
sem sorteio.

Sorteio aleatorio seria um erro grave aqui: amostras da mesma sessao de ensaio
foram coletadas com segundos de diferenca e cairiam dos dois lados. O vizinho
mais proximo de uma leitura de teste seria praticamente ela mesma, e a acuracia
sairia inflada e falsa.

| Split | Leituras | Periodo |
| --- | ---: | --- |
| `holdout` | 9.061 | 10/06/2026 a 16/06/2026 |
| `train` | 157.735 | 30/04/2026 a 09/06/2026 |

## Distribuicao por familia

| Familia | Descricao | Problema | Total | Treino | Teste | Subtipos |
| --- | --- | :---: | ---: | ---: | ---: | ---: |
| `rolamento` | Defeito em rolamento (pista interna, externa, esferas ou combinado) | sim | 60.779 | 57.579 | 3.200 | 4 |
| `eccentric_rotor` | Centro geometrico do rotor deslocado do centro de rotacao | sim | 16.497 | 15.897 | 600 | 1 |
| `normal` | Operacao normal | nao | 15.058 | 13.758 | 1.300 | 1 |
| `cocked_rotor` | Rotor inclinado em relacao ao eixo de rotacao | sim | 14.275 | 13.675 | 600 | 1 |
| `desbalanceamento` | Distribuicao desigual de massa no rotor | sim | 13.237 | 11.779 | 1.458 | 2 |
| `ventoinha` | Defeito na ventoinha do motor | sim | 12.299 | 12.299 | 0 | 1 |
| `polia` | Defeito em polia (excentricidade, desbalanceamento, desgaste) | sim | 12.000 | 12.000 | 0 | 1 |
| `correia` | Defeito no sistema de transmissao por correia | sim | 11.999 | 11.999 | 0 | 1 |
| `desalinhamento` | Eixos do motor e da carga fora de alinhamento | sim | 9.178 | 8.148 | 1.030 | 1 |
| `falta_fase` | Operacao com falta de fase na alimentacao eletrica | sim | 800 | 0 | 800 | 1 |
| `motor_desligado` | Motor parado | nao | 497 | 497 | 0 | 1 |
| `teste` | Coleta de teste | nao | 101 | 97 | 4 | 1 |
| `baseline` | Coleta de referencia | nao | 69 | 0 | 69 | 1 |
| `acelerando` | Transiente de aceleracao | nao | 7 | 7 | 0 | 1 |

### Familias ausentes de um dos lados

O corte temporal e honesto, mas nao e equilibrado -- e isso tem consequencia
direta no que o sistema consegue fazer.

**Sem historico** — aparecem no conjunto de teste e nao no de treino. Nenhuma
busca por similaridade poderia acerta-las; o comportamento correto e recusar:

- `falta_fase`

**Sem leitura de teste** — existem no historico, mas nao no periodo reservado
para avaliacao. Nao podem ser demonstradas, e a interface nao as oferece:

- `ventoinha`
- `polia`
- `correia`

## Regimes de rotacao

| RPM | Leituras |
| ---: | ---: |
| 0 | 658 |
| 500 | 55.857 |
| 1000 | 53.414 |
| 2000 | 55.160 |
| 3000 | 1.707 |

Vibracao escala com a rotacao (F = m·r·ω², conforme o Doc3), entao o RPM entra
no vetor de features: comparar uma leitura a 2000 rpm com outra a 500 rpm sem
esse eixo produziria vizinho sem sentido fisico.

## Colunas

O CSV traz 24 colunas numericas. 16 entram no vetor de
similaridade, 18 sao persistidas para exibicao e
7 sao descartadas por redundancia.

### No vetor de similaridade

- `z_rms_velocity_mm_s`
- `x_rms_velocity_mm_s`
- `z_peak_acceleration_g`
- `x_peak_acceleration_g`
- `z_rms_acceleration_g`
- `x_rms_acceleration_g`
- `z_high_freq_rms_accel_g`
- `x_high_freq_rms_accel_g`
- `z_kurtosis`
- `x_kurtosis`
- `z_crest_factor`
- `x_crest_factor`
- `z_peak_vel_comp_freq_hz`
- `x_peak_vel_comp_freq_hz`
- `temperature_c`
- `rpm`

### Descartadas

Conversao de unidade — correlacao >= 0,999999 com a coluna metrica mantida:

- `z_rms_velocity_in_s`
- `x_rms_velocity_in_s`
- `z_peak_velocity_in_s`
- `x_peak_velocity_in_s`
- `temperature_f`

Coluna derivada — `peak_velocity` e o RMS multiplicado por sqrt(2), calculado
pelo firmware assumindo sinal senoidal. Correlacao 1,000000; nao carrega
informacao alem do RMS:

- `z_peak_velocity_mm_s`
- `x_peak_velocity_mm_s`

Detalhamento da auditoria de redundancia em
[SPEC-FEAT-003](../SPEC-FEAT-003/spec.md).
