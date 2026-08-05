# SPEC-FEAT-006 — Painel de eventos similares

| | |
| --- | --- |
| **App** | frontend |
| **Épico** | Análise e chat |
| **Atende** | §3 — quantidade de eventos similares, distribuição, frequência, contexto operacional |
| **Depende de** | `SPEC-FEAT-005`, `backend/SPEC-FEAT-005` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

Materializa exatamente a lista de informações que o §3 do desafio pede como saída da busca
por similaridade. É a evidência que sustenta o diagnóstico e antecede a prescrição.

## Escopo

- Tabela dos vizinhos mais próximos: identificador, data, família, similaridade e RPM.
- Contagem de eventos similares por família, com a distribuição do voto visível — deixa claro
  se o diagnóstico foi unânime ou disputado.
- Linha do tempo dos eventos similares, com o evento em análise posicionado nela.
- Bloco de contexto operacional: faixa de RPM e temperatura da vizinhança comparada à do
  evento analisado.
- Frequência de ocorrência e intervalo médio entre eventos.

## Fora de escopo

- Inspeção da forma de onda bruta — não está no dataset.

## Decisões técnicas

- **Distribuição do voto exposta, não só a família vencedora.** Um diagnóstico 51% × 49% e
  outro 98% × 2% não merecem a mesma leitura, e a interface precisa deixar isso evidente.
- **Similaridade em barra e em número.** A barra dá leitura imediata; o número permite
  comparação precisa na discussão técnica.

## Contrato

```ts
POST /api/events/similar (SensorEvent) -> {
  neighbors, familyCounts, timeline,
  frequencyPerDay, meanIntervalHours, operatingContext
}
```
