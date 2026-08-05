# SPEC-FEAT-007 — Chat prescritivo com citações

| | |
| --- | --- |
| **App** | frontend |
| **Épico** | Análise e chat |
| **Atende** | §3 — modelo de linguagem para auxílio; OBS 3 — interação com o chat na apresentação |
| **Depende de** | `SPEC-FEAT-005`, `backend/SPEC-FEAT-011` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

A observação 3 do enunciado é explícita: espera-se interação mínima com o modelo durante a
apresentação. Este é o componente que será operado ao vivo, e onde o critério "alucinação do
modelo" vai ser julgado.

## Escopo

- Conversa com histórico, ancorada no evento em análise (o contexto do evento acompanha as
  perguntas seguintes).
- Resposta renderizada por seções: diagnóstico, evidência, inspeção, correção, validação.
- **Citações clicáveis** — `[Doc2, p. 4]` abre um painel lateral com o trecho exato recuperado,
  com destaque. É o que transforma "confie no modelo" em "verifique você mesmo".
- Indicador de embasamento da resposta (score de grounding) e lista do que foi removido por
  falta de suporte.
- Perguntas sugeridas conforme o diagnóstico, para agilizar a demonstração.
- Resposta em fluxo (streaming) quando disponível.

## Fora de escopo

- Conversa livre sem evento associado — o sistema é prescritivo, ancorado em um evento.
- Histórico persistido entre sessões.

## Decisões técnicas

- **Citação clicável mostrando o trecho original.** É a defesa mais concreta contra a
  acusação de alucinação: o avaliador confere na hora, contra o PDF.
- **Score de embasamento visível.** Assume a incerteza em vez de escondê-la — postura mais
  forte que fingir certeza absoluta.
- **Resposta seccionada em vez de bolha de texto.** Espelha a estrutura da saída do backend e
  é o formato que um técnico consegue seguir passo a passo.

## Contrato

```ts
POST /api/chat { eventId?, event?, messages[] } -> {
  answer: PrescriptiveAnswer, citations, grounding, timings
}
```
