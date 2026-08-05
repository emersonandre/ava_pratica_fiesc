# SPEC-FEAT-004 — Ingestão do banner.csv com split temporal

| | |
| --- | --- |
| **App** | backend |
| **Épico** | Infraestrutura e dados |
| **Atende** | §2, §3 — dados dos equipamentos monitorados |
| **Depende de** | `SPEC-FEAT-002`, `SPEC-FEAT-003` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

166.796 registros precisam ir para o banco já normalizados e vetorizados, com um recorte de
avaliação honesto. O dataset oferece um corte temporal natural: **todo rótulo com prefixo
`new_` ocorre entre 10 e 16/jun/2026, e todo o restante é ≤ 09/jun/2026**. Isso permite um
holdout sem vazamento e sem sorteio artificial.

## Escopo

- Leitura em chunks de `dados/banner.csv` (evita carregar 31 MB de uma vez sem necessidade).
- Aplicação de SPEC-FEAT-002 (taxonomia) e SPEC-FEAT-003 (features).
- Gravação em `sensor_events`: identificação, timestamp, rótulos bruto e canônico, família,
  `is_problem`, colunas métricas originais e o vetor padronizado em `vector(13)`.
- Marcação de `split`: `train` (≤ 09/jun) e `holdout` (rótulos `new_*`, 10–16/jun).
- Índice HNSW com operador de distância cosseno sobre a coluna vetorial.
- Upsert por `id` — reexecução não duplica.

## Fora de escopo

- Ingestão em streaming/tempo real (descrita na arquitetura de implantação).
- Uso do `banner.xlsx` — mesma base, formato menos adequado a ETL.

## Decisões técnicas

- **Split temporal, nunca aleatório.** Sorteio embaralharia amostras da mesma sessão de
  ensaio (coletadas com segundos de diferença) entre treino e teste; o vizinho mais próximo
  seria praticamente o mesmo registro e a acurácia sairia inflada e falsa.
- **`holdout` definido pelo prefixo `new_` E pela data**, não só pelo nome — a regra é
  verificada na ingestão, não assumida. Divergência aborta a carga.
- **Distância cosseno.** Interessa o *padrão* de vibração (forma do vetor), com magnitude já
  tratada pela padronização.
- **Índice HNSW parcial, restrito a `split = 'train'`.** O HNSW do pgvector faz *pós-filtro*:
  encontra os k vizinhos e só depois aplica o `WHERE`. Com índice sobre a tabela inteira e
  consulta partindo de um evento do holdout, os vizinhos mais próximos são os próprios
  registros do holdout (mesma sessão de ensaio) — todos descartados pelo filtro, e a busca
  **retorna vazio**. Comprovado na prática durante a implementação. Como buscar dentro do
  holdout seria vazamento, o filtro entra no próprio índice: corrige o resultado e ainda
  deixa o índice menor.

## Contrato

```sql
CREATE TABLE sensor_events (
    id              BIGINT PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL,
    raw_fault       TEXT NOT NULL,
    canonical_fault TEXT NOT NULL,
    fault_family    TEXT NOT NULL,
    is_problem      BOOLEAN NOT NULL,
    split           TEXT NOT NULL CHECK (split IN ('train','holdout')),
    rpm             REAL, temperature_c REAL, ...
    features        VECTOR(18) NOT NULL
);

-- Indice PARCIAL: toda busca por similaridade e restrita ao historico.
CREATE INDEX ix_sensor_events_features_hnsw
    ON sensor_events USING hnsw (features vector_cosine_ops)
    WHERE split = 'train';
```
