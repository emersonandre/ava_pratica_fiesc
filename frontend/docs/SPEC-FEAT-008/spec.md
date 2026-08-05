# SPEC-FEAT-008 — Estado de falha não documentada

| | |
| --- | --- |
| **App** | frontend |
| **Épico** | Análise e chat |
| **Atende** | §3 — reportar ausência de documento e sugerir registro |
| **Depende de** | `SPEC-FEAT-007`, `backend/SPEC-FEAT-008`, `SPEC-FEAT-004` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

A regra de recusa do enunciado precisa de tratamento visual próprio. Se a recusa parecer um
erro do sistema, o avaliador lê como falha; se parecer uma decisão deliberada e informada,
lê como o comportamento correto — que é o que é.

## Escopo

- Estado visual distinto (não é erro, não é sucesso): a análise estatística é entregue, a
  prescrição é explicitamente retida.
- Texto alinhado ao enunciado: não existe documentação para o problema identificado; sugere
  registrar um novo documento para o defeito.
- Mesmo sem prescrição, exibe o que o sistema sabe: família diagnosticada, quantidade de
  eventos similares, distribuição temporal.
- Ação direta de registrar documento, com a família já preenchida (SPEC-FEAT-004).
- **Distinção entre três situações**, com mensagens diferentes: falha sem documento; evento
  fora de distribuição; estado operacional (não é problema).

## Fora de escopo

- Sugerir procedimento "genérico" de manutenção como paliativo — seria exatamente a
  alucinação que a regra existe para impedir.

## Decisões técnicas

- **Recusa desenhada como resultado, não como erro.** É o comportamento correto do sistema, e
  a interface precisa comunicar isso com clareza.
- **Três mensagens distintas para três causas distintas.** Colapsá-las em "não sei" desperdiça
  a informação mais interessante da solução.

## Contrato

```ts
coverage.reason: "covered" | "no_document" | "state_not_problem" | "out_of_distribution"
```
