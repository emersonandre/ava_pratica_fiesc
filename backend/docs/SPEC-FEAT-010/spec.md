# SPEC-FEAT-010 — Recuperação de contexto para prescrição

| | |
| --- | --- |
| **App** | backend |
| **Épico** | RAG e LLM |
| **Atende** | §3 — consultar manuais e procedimentos relacionados |
| **Depende de** | `SPEC-FEAT-007`, `SPEC-FEAT-008` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

Busca puramente semântica erra de um jeito específico e perigoso neste domínio: os seis
documentos compartilham vocabulário quase idêntico ("vibração elevada", "aquecimento nos
mancais", "desgaste de rolamentos", "afrouxamento de parafusos"). Uma consulta sobre correia
recupera com folga trechos de desbalanceamento. A resposta sairia fluente, citada — e errada.

## Escopo

- Busca híbrida: **filtro rígido** pelos documentos que cobrem a família diagnosticada
  (SPEC-FEAT-008) + ranqueamento semântico dentro desse subconjunto.
- Priorização das seções acionáveis (procedimento, correção, validação) sobre as
  introdutórias, quando a intenção é prescritiva.
- Limite de contexto por orçamento de tokens, mantendo chunks inteiros.
- Cada trecho retornado carrega documento, página, seção e score.

## Fora de escopo

- Busca cross-família ("veja também documentos relacionados") — contraria a regra de §3.

## Decisões técnicas

- **Filtro por família é rígido, não um reforço de score.** Um peso alto ainda deixaria passar
  documento errado; o corte duro elimina a classe inteira de erro.
- **Ordenação por seção depende da intenção.** Pergunta de diagnóstico privilegia "Sintomas";
  pedido de correção privilegia "Procedimento".

## Contrato

```python
class RetrievedChunk(BaseModel):
    document: str
    page_start: int
    page_end: int
    section: str | None
    content: str
    score: float

def retrieve(query: str, family: str, *, budget_tokens: int) -> list[RetrievedChunk]: ...
```
