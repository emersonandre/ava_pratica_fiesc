# SPEC-FEAT-005 — Motor de similaridade histórica

| | |
| --- | --- |
| **App** | backend |
| **Épico** | Similaridade e documentos |
| **Atende** | §3 — localizar ocorrências passadas com características próximas |
| **Depende de** | `SPEC-FEAT-004` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

É o coração do desafio: dado um evento novo, encontrar no histórico os registros de
comportamento semelhante e devolver o contexto que o desafio pede — quantidade de eventos
similares, distribuição ao longo do tempo, frequência de ocorrência e contexto operacional.
O desafio é explícito: a solução **não depende de classificação prévia de falhas conhecidas**,
e sim de identificação de padrões similares.

## Escopo

- KNN por distância cosseno no pgvector, restrito a `split = 'train'`.
- Agregações sobre a vizinhança:
  - contagem de eventos similares por família;
  - série temporal das ocorrências (diária);
  - frequência de ocorrência e intervalo médio entre eventos (MTBF empírico);
  - contexto operacional (faixa de RPM e de temperatura dos vizinhos).
- Diagnóstico por **voto ponderado pela similaridade** dos `k` vizinhos.
- Confiança = concentração do voto (a família vencedora domina ou o voto está dividido?).
- **Detecção de fora de distribuição:** se a distância do vizinho mais próximo ultrapassa o
  limiar calibrado, o evento é reportado como *padrão não observado no histórico* — não é
  empurrado para a família mais próxima.

## Fora de escopo

- Treinar classificador supervisionado. O enunciado pede similaridade, não classificação —
  e um classificador não conseguiria responder "quantos eventos parecidos já aconteceram".

## Decisões técnicas

- **Voto ponderado por similaridade, não maioria simples.** Com `k` fixo, vizinhos distantes
  votariam com o mesmo peso dos próximos.
- **Limiar de fora de distribuição calibrado empiricamente**, a partir da distribuição de
  distâncias intra-família no split de treino (ex.: percentil alto), e registrado no relatório.
- **Vizinhos vêm só do treino.** Buscar dentro do holdout durante a demonstração seria
  vazamento e invalidaria a métrica apresentada na entrevista.

## Contrato

```python
class SimilarityResult(BaseModel):
    diagnosed_family: str | None      # None quando fora de distribuição
    confidence: float
    out_of_distribution: bool
    neighbors: list[Neighbor]         # id, created_at, family, similarity
    family_counts: dict[str, int]
    timeline: list[TimelinePoint]     # data, contagem
    frequency_per_day: float
    mean_interval_hours: float | None
    operating_context: OperatingContext   # faixas de rpm e temperatura
```
