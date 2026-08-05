# SPEC-FEAT-014 — Registro de novo documento de falha

| | |
| --- | --- |
| **App** | backend |
| **Épico** | API, seguranca e qualidade |
| **Atende** | §3 — sugerir ao usuário registrar um novo documento para o defeito |
| **Depende de** | `SPEC-FEAT-007`, `SPEC-FEAT-008` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

O enunciado não pede só recusar: pede **sugerir ao usuário registrar um novo documento**.
Fechar esse ciclo transforma a recusa em fluxo de trabalho, e dá a demonstração mais forte
da entrevista — a mesma pergunta, recusada antes e respondida depois do upload.

## Escopo

- `POST /api/documents` com upload de PDF + família de falha alvo.
- Pipeline reaproveitado: extração/OCR (SPEC-FEAT-006) → chunking + embeddings (SPEC-FEAT-007)
  → vínculo de cobertura (SPEC-FEAT-008).
- Estado de indexação consultável (`pending` → `processing` → `indexed` | `failed`).
- Deduplicação por hash de conteúdo — reenviar o mesmo arquivo não duplica chunks.
- Recálculo da cobertura ao final, sem reiniciar a API.

## Fora de escopo

- Fluxo de aprovação/revisão editorial do documento.
- Versionamento de documento (substituir revisão anterior).

## Decisões técnicas

- **Indexação síncrona nesta entrega.** Os documentos são pequenos (~10 páginas); uma fila
  (Celery/RQ) adicionaria infraestrutura sem ganho perceptível. A alternativa assíncrona fica
  registrada no documento de arquitetura.
- **Família informada pelo usuário, não inferida.** Quem registra sabe a que defeito o
  documento se refere; inferir seria introduzir erro justamente no mecanismo antialucinação.

## Contrato

```
POST /api/documents  (multipart)
  file: application/pdf
  fault_family: str
  title: str

201 → { document_id, status, chunks, pages, method, coverage_updated: bool }
```
