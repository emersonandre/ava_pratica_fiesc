# SPEC-FEAT-011 — Geração prescritiva com citações

| | |
| --- | --- |
| **App** | backend |
| **Épico** | RAG e LLM |
| **Atende** | §3 — demonstrar como corrigir o problema ocorrido |
| **Depende de** | `SPEC-FEAT-005`, `SPEC-FEAT-009`, `SPEC-FEAT-010` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

A saída precisa ser **prescritiva**, não descritiva: o operador quer saber o que fazer, em que
ordem, e como validar que o problema foi resolvido. Texto corrido dificulta a leitura em chão
de fábrica e dificulta a verificação automática de embasamento.

## Escopo

Resposta estruturada, com campos fixos:

| Campo | Conteúdo |
| --- | --- |
| `diagnostico` | Família identificada e o raciocínio a partir dos vizinhos históricos |
| `evidencia` | Quantidade de eventos similares, período, frequência e contexto operacional |
| `inspecao` | Verificações a fazer antes de intervir, cada uma com citação |
| `correcao` | Passos de correção ordenados, cada um com citação |
| `validacao` | Critérios para confirmar que a falha foi corrigida |
| `citacoes` | Lista de `{documento, página, seção}` referenciada no texto |
| `avisos` | Limitações e pontos que exigem julgamento humano |

Prompt em português, com instrução explícita de responder **somente** a partir do contexto
recuperado e de se abster quando o contexto não sustentar a afirmação.

## Fora de escopo

- Estimar custo, tempo de parada ou peças — não há dado que sustente.
- Emitir ordem de serviço em sistema de manutenção.

## Decisões técnicas

- **Saída estruturada, não texto livre.** Permite verificar embasamento por campo
  (SPEC-FEAT-012), renderizar bem no frontend e reduzir divagação.
- **Citação por passo, não por resposta.** Uma citação global no rodapé não prova que
  *aquele* passo veio do manual.
- **Evidência estatística e prescrição textual em campos separados.** Os números vêm do
  banco (SPEC-FEAT-005), não do modelo; separar deixa explícito o que o LLM não inventou.

## Contrato

```python
class PrescriptiveAnswer(BaseModel):
    diagnostico: str
    evidencia: EvidenceBlock          # preenchido por código, não pelo LLM
    inspecao: list[ActionStep]        # texto + citações
    correcao: list[ActionStep]
    validacao: list[ActionStep]
    citacoes: list[Citation]
    avisos: list[str]
```
