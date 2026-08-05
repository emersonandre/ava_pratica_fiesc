# SPEC-FEAT-003 — Gráficos analíticos

| | |
| --- | --- |
| **App** | frontend |
| **Épico** | Base e dashboard |
| **Atende** | §3 — distribuição ao longo do tempo, frequência de ocorrência |
| **Depende de** | `SPEC-FEAT-002` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

O enunciado pede nominalmente distribuição temporal e frequência de ocorrência. São os
gráficos que sustentam a conversa sobre padrão de falha na entrevista.

## Escopo

- Linha do tempo de ocorrências por dia, empilhada por família, com seleção de período.
- Distribuição de uma métrica de vibração por família (dispersão ou caixa) — evidencia
  visualmente por que as famílias são separáveis no espaço de features.
- Frequência de ocorrência e intervalo médio entre eventos por família.
- Marcação visual do corte entre histórico (≤ 09/jun) e holdout (10–16/jun) — deixa o rigor
  metodológico visível em vez de precisar ser explicado.

## Fora de escopo

- Gráficos 3D ou animações — atrapalham a leitura de dado técnico.
- Exportação de imagem dos gráficos.

## Decisões técnicas

- **Recharts.** Suficiente para os tipos usados, componível em React, sem o peso e a curva do D3.
- **Eixos sempre rotulados com unidade.** Público técnico: `mm/s` sem rótulo é ruído.
- **Paleta de famílias estável entre gráficos e telas.** A mesma família mantém a mesma cor
  em toda a aplicação; cor inconsistente entre painéis confunde mais do que ajuda.

## Contrato

```ts
GET /api/stats/timeline?family=&from=&to= -> { date, family, count }[]
```
