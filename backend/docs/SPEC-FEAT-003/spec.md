# SPEC-FEAT-003 — Feature engineering dos sinais de vibração

| | |
| --- | --- |
| **App** | backend |
| **Épico** | Infraestrutura e dados |
| **Atende** | §3 — análise de novos conjuntos de dados |
| **Depende de** | `SPEC-FEAT-002` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

O dataset traz 24 colunas numéricas, mas várias são **a mesma grandeza física em outra
unidade**. Auditoria sobre os 166.796 registros confirmou:

| Par | Correlação | Razão |
| --- | ---: | ---: |
| `z_rms_velocity_in_s` × `z_rms_velocity_mm_s` | 0,999999 | 25,4114 |
| `x_rms_velocity_in_s` × `x_rms_velocity_mm_s` | 0,999999 | 25,4079 |
| `z_peak_velocity_in_s` × `z_peak_velocity_mm_s` | 1,000000 | 25,4081 |
| `x_peak_velocity_in_s` × `x_peak_velocity_mm_s` | 1,000000 | 25,4056 |
| `temperature_f` × `temperature_c` | 0,999999 | relação afim |

Em uma busca por distância, manter as duas versões dá peso dobrado àquela grandeza e
enviesa o vizinho mais próximo.

## Escopo

- Auditoria de redundância: verificar numericamente cada par suspeito no dataset completo.
- Seleção do vetor de features — **18 dimensões**, sistema métrico: velocidade RMS e de pico,
  aceleração de pico e RMS, aceleração RMS de alta frequência, kurtosis, crest factor e
  frequência da componente de pico, nos eixos X e Z (16), mais temperatura em °C e RPM.
- Padronização com `StandardScaler` ajustado **apenas no split de treino** e persistido
  em `artifacts/scaler.joblib`.
- A mesma função de transformação serve ingestão e inferência (sem código duplicado).

## Fora de escopo

- Redução de dimensionalidade (PCA): 18 dimensões não pressionam o índice HNSW e a
  interpretabilidade por sensor vale mais na entrevista.
- Extração de features a partir de forma de onda bruta — o dataset já entrega agregados.

## Decisões técnicas

- **Descartar as colunas imperiais e Fahrenheit.** São transformações lineares exatas das
  métricas; carregam zero informação nova e distorcem a distância.
- **`StandardScaler` em vez de min-max.** As caudas são pesadas (kurtosis, crest factor);
  min-max deixaria a escala refém de outliers.
- **RPM entra como feature.** Vibração escala com rotação (F = m·r·ω², conforme o Doc3);
  comparar um evento a 1000 rpm com outro a 0 rpm sem esse eixo produz vizinho sem sentido.
- **Registros com `motor_desligado` (RPM = 0) ficam fora do ajuste do scaler**, mas seguem
  no banco: são estado válido, não amostra representativa de operação.

## Contrato

```python
FEATURE_COLUMNS: tuple[str, ...]   # ordem estável — define o layout do vetor

def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame: ...
def fit_scaler(df: pd.DataFrame) -> StandardScaler: ...
def to_vector(payload: dict) -> np.ndarray: ...   # usado na inferência
```
