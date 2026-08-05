# SPEC-FEAT-008 — Mapa falha→documento e gate de cobertura

| | |
| --- | --- |
| **App** | backend |
| **Épico** | Similaridade e documentos |
| **Atende** | §3 — regra explícita de recusa quando não há documento |
| **Depende de** | `SPEC-FEAT-002`, `SPEC-FEAT-007` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

O enunciado é literal: *"O sistema deve se deter unicamente a problemas que possuem
documentos, caso contrário deve reportar que ainda não existe o problema identificado e
sugerir ao usuário para registrar um novo documento para o defeito."*

Isso é regra de negócio, e regra de negócio não se implementa como pedido educado no prompt.

Cobertura conhecida pela leitura dos PDFs:

| Família | Documento | Situação |
| --- | --- | --- |
| `desalinhamento` | Doc2 | coberto |
| `desbalanceamento` | Doc3 | coberto |
| `correia` | Doc4 | coberto |
| `polia` | Doc5 | coberto |
| `cocked_rotor` | Doc6 | coberto |
| `rolamento` | Doc1 — a confirmar via OCR (SPEC-FEAT-006) | a confirmar |
| `eccentric_rotor`, `ventoinha`, `falta_fase` | — | **descoberto** |

A família `rolamento` sozinha soma ~37 mil registros — a maior massa do dataset. Se o Doc1
não a cobrir, o caso de recusa é **real**, não fabricado para a demonstração.

## Escopo

- Tabela `fault_document_coverage` ligando família canônica → documentos que a cobrem.
- Montagem por âncoras semânticas (consultas-sonda por família contra o índice) **com
  revisão explícita registrada** — não por inferência do LLM.
- Função `check_coverage(family) -> Coverage` chamada **antes** de qualquer chamada ao LLM.
- Resposta estruturada de recusa quando não há cobertura, incluindo o que se sabe do evento
  (família diagnosticada, número de ocorrências similares) e a orientação de registrar documento.
- Recálculo automático da cobertura após upload de documento (SPEC-FEAT-014).

## Fora de escopo

- Deixar o LLM decidir se tem informação suficiente. É justamente o comportamento que a
  entrevista avalia como alucinação.

## Decisões técnicas

- **Gate determinístico em código, antes do LLM.** Se não há cobertura, o modelo sequer é
  chamado — não há como alucinar o que não foi perguntado.
- **Mapa revisado por humano e versionado.** Auditável e defensável na entrevista.
- **Recusa é informativa, não um beco sem saída.** Devolve a análise estatística que o
  sistema *tem* e pede o documento que falta.

## Contrato

```python
class Coverage(BaseModel):
    family: str
    is_covered: bool
    documents: list[DocumentRef]
    reason: Literal["covered", "no_document", "state_not_problem", "out_of_distribution"]
```
