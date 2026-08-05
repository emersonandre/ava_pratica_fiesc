# SPEC-FEAT-012 — Guarda anti-alucinação

| | |
| --- | --- |
| **App** | backend |
| **Épico** | RAG e LLM |
| **Atende** | Critério de entrevista: "Alucinação do modelo" |
| **Depende de** | `SPEC-FEAT-008`, `SPEC-FEAT-011` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

"Alucinação do modelo" é critério **explícito** de avaliação da entrevista. Confiar apenas na
instrução do prompt é frágil e indefensável sob questionamento. A defesa aqui é em
profundidade, com um caso de teste para cada camada.

## Escopo

**Camada 1 — Gate determinístico (SPEC-FEAT-008).** Sem documento, o LLM não é chamado.

**Camada 2 — Prompt restritivo.** Contexto delimitado, instrução de responder somente a
partir dele e de declarar quando a informação não está disponível.

**Camada 3 — Verificação de embasamento pós-geração.** Cada afirmação técnica gerada é
conferida contra os trechos recuperados; afirmação sem suporte é removida da resposta e
registrada em `avisos`.

**Camada 4 — Recusa de fora de domínio.** Pergunta alheia à manutenção industrial é recusada
com educação e sem tentativa de resposta.

Suíte adversarial versionada, com o resultado publicado no README.

## Fora de escopo

- Garantia formal de ausência de alucinação — não existe. O objetivo é reduzir a taxa e
  tornar cada resposta auditável.

## Decisões técnicas

- **Verificação pós-geração mesmo custando uma chamada a mais.** É o critério avaliado; a
  latência extra vale menos que uma resposta inventada na demonstração ao vivo.
- **Remover em vez de marcar, quando a afirmação é acionável.** Uma instrução de manutenção
  sem embasamento é risco físico; um aviso discreto não basta.
- **Casos adversariais versionados.** Permite mostrar o comportamento na entrevista em vez
  de afirmá-lo.

## Contrato

```python
class GroundingReport(BaseModel):
    total_claims: int
    grounded: int
    removed: list[str]
    score: float          # grounded / total_claims

def verify_grounding(answer: PrescriptiveAnswer, context: list[RetrievedChunk]) -> tuple[PrescriptiveAnswer, GroundingReport]: ...
```
