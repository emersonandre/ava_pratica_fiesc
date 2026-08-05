# Motor de similaridade -- avaliacao no holdout

> Gerado por `python manage.py report similaridade`.
> Evidencia da [SPEC-FEAT-005](../SPEC-FEAT-005/spec.md).

## Protocolo

| | |
| --- | --- |
| Historico (treino) | 157.735 eventos |
| Avaliados (holdout) | 3.000 eventos |
| Vizinhos (k) | 50 |
| Metrica | distancia cosseno, voto ponderado pela similaridade |

O holdout e o corte temporal natural do dataset (rotulos `new_*`, 10 a 16/jun). Nenhum vizinho vem dele -- o indice HNSW e parcial sobre `split = 'train'`.

## Resultado bruto, sem portao de confianca

**Acuracia: 40.2%** sobre 3.000 eventos.

### Familias impossiveis por construcao

Estas familias aparecem no holdout e **nao existem no historico**, entao nenhuma busca por similaridade poderia acerta-las. O comportamento correto e recusar, nao adivinhar:

- `baseline` (20 eventos)
- `falta_fase` (244 eventos)

## Acerto por familia

| Familia | Eventos | Acerto | Previsao mais comum |
| --- | ---: | ---: | --- |
| `baseline` | 20 | 0.0% | `motor_desligado` |
| `cocked_rotor` | 187 | 0.5% | `rolamento` |
| `desalinhamento` | 345 | 0.0% | `rolamento` |
| `desbalanceamento` | 497 | 28.8% | `desbalanceamento` |
| `eccentric_rotor` | 195 | 9.2% | `rolamento` |
| `falta_fase` | 244 | 0.0% | `rolamento` |
| `normal` | 448 | 24.3% | `rolamento` |
| `rolamento` | 1063 | 88.1% | `rolamento` |
| `teste` | 1 | 0.0% | `motor_desligado` |

## Portao de confianca: precisao contra cobertura

O sistema so emite diagnostico quando a concordancia da vizinhanca supera o limiar. Abaixo dele, entrega os eventos similares e se abstem.

| Limiar | Cobertura | Precisao |
| ---: | ---: | ---: |
| 0.00 | 100.0% | 40.2% |
| 0.50 | 74.0% | 46.8% |
| 0.60 | 59.1% | 52.5% |
| 0.70 **(configurado)** | 46.7% | 59.2% |
| 0.80 | 35.1% | 64.0% |
| 0.90 | 24.8% | 70.0% |
| 0.95 | 19.2% | 73.4% |

### O portao recusa as familias sem historico?

| Familia | Eventos | Recusados |
| --- | ---: | ---: |
| `baseline` | 20 | 55.0% |
| `falta_fase` | 244 | 59.4% |

## Leitura dos resultados

**A confianca vem da concordancia da vizinhanca, nao da distancia.** Medindo o portao por distancia ao vizinho mais proximo, a precisao *cai* conforme os vizinhos ficam mais proximos (18% em distancia <= 0,5, contra 39% sem portao nenhum). A razao e que os vizinhos mais proximos caem no cluster dominante de `rolamento`, 36% do historico -- proximidade alta muitas vezes significa absorcao pela classe majoritaria. O plano inicial era usar distancia como sinal de confianca; a medicao mostrou que produziria o comportamento oposto ao desejado.

**O teto nao e do metodo, e dos dados.** Um classificador supervisionado (HistGradientBoosting, 200 iteracoes) treinado nas mesmas features atinge 39,8% no holdout contra 78,8% no proprio treino. KNN e o classificador chegam ao mesmo lugar: existe deslocamento de distribuicao real entre o historico e as sessoes `new_*`. As medias padronizadas da familia `rolamento` deslocam em media 0,45 desvios entre os dois splits, chegando a 1,46 na temperatura, e o holdout opera em um regime de RPM praticamente ausente do historico.

**Por isso a abstencao e o comportamento correto.** Prescrever intervencao fisica em equipamento com 40% de acerto e pior que admitir desconhecimento. O portao troca cobertura por precisao de forma explicita e mensuravel, e os eventos similares continuam disponiveis para analise humana mesmo quando o diagnostico e retido.
