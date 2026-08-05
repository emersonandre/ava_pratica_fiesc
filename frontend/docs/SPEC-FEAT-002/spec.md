# SPEC-FEAT-002 — Dashboard de indicadores

| | |
| --- | --- |
| **App** | frontend |
| **Épico** | Base e dashboard |
| **Atende** | §3 — apresentação visual dos resultados; DIF — Dashboards |
| **Depende de** | `SPEC-FEAT-001` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

Primeira tela da apresentação. Precisa responder em segundos: qual a situação do parque,
quais falhas dominam, e o que a base de conhecimento cobre.

## Escopo

- Cartões de indicador: total de eventos monitorados, eventos classificados como problema,
  número de famílias de falha distintas, cobertura documental (famílias cobertas / total),
  período coberto pelo histórico.
- Ranking das famílias de falha por número de ocorrências, com o status de cobertura
  documental em cada linha.
- Destaque para as famílias **sem documento** — é a lacuna acionável, e o gancho para a
  narrativa da entrevista.
- Atalho de cada família para a análise detalhada.

## Fora de escopo

- Filtro por equipamento/linha — o dataset é de uma única máquina rotativa.
- Alertas em tempo real.

## Decisões técnicas

- **Cobertura documental como indicador de primeira linha.** É o diferencial conceitual da
  solução: o sistema sabe o que não sabe.
- **Números vindos de uma única chamada (`/api/stats/overview`).** Evita cascata de
  requisições e mantém os cartões consistentes entre si.

## Contrato

```ts
GET /api/stats/overview -> {
  totalEvents, problemEvents, familyCount,
  coveredFamilies, uncoveredFamilies,
  periodStart, periodEnd,
  ranking: { family, count, covered, documents }[]
}
```
