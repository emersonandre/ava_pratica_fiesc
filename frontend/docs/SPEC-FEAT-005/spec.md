# SPEC-FEAT-005 — Análise de evento e simulador

| | |
| --- | --- |
| **App** | frontend |
| **Épico** | Análise e chat |
| **Atende** | Critério de entrevista: demonstração com dados de teste |
| **Depende de** | `SPEC-FEAT-001`, `backend/SPEC-FEAT-013` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

Ponto de entrada da demonstração ao vivo. Precisa aceitar o JSON de sensor do enunciado e,
principalmente, permitir puxar um evento real do holdout — mostrar o sistema acertando (ou
errando) sobre dado que ele nunca viu é mais forte que qualquer slide.

## Escopo

- Editor de JSON com validação e mensagem de erro apontando o campo problemático.
- Botão "carregar evento do holdout": busca um evento real de 10–16/jun via
  `/api/events/sample`, com filtro opcional por família.
- Execução da análise com exibição do rótulo real ao lado do diagnóstico — acerto e erro
  ficam visíveis, sem maquiagem.
- Cartão de diagnóstico: família, confiança, sinalização de fora de distribuição.
- Tempo de cada etapa exibido (similaridade, recuperação, geração, verificação).

## Fora de escopo

- Upload de CSV em lote para análise.
- Edição gráfica de valores por sliders.

## Decisões técnicas

- **Mostrar o rótulo real junto do diagnóstico.** Esconder o gabarito numa demonstração
  técnica é o que produz a pergunta constrangedora na entrevista. Expor demonstra confiança
  e permite discutir os erros.
- **Amostra vem do holdout, nunca do treino.** Demonstrar sobre dado de treino inflaria o
  resultado e seria vazamento óbvio.

## Contrato

```ts
GET  /api/events/sample?family=&split=holdout -> SensorEvent
POST /api/events/analyze (SensorEvent) -> AnalyzeResponse
```
