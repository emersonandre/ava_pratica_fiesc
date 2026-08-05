# SPEC-FEAT-004 — Gestão de documentos

| | |
| --- | --- |
| **App** | frontend |
| **Épico** | Base e dashboard |
| **Atende** | §3 — registrar novo documento; DIF — Dashboards |
| **Depende de** | `SPEC-FEAT-001`, `backend/SPEC-FEAT-014` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

Contraparte visual do ciclo de cobertura documental: mostrar o que a base conhece, o que
falta, e permitir preencher a lacuna.

## Escopo

- Lista de documentos indexados: título, família vinculada, páginas, número de chunks,
  método de extração (texto ou OCR) e estado da indexação.
- Sinalização dos documentos processados por OCR — informação relevante de confiabilidade.
- Upload de novo documento: arquivo, família alvo e título, com progresso e resultado.
- Painel de lacunas: famílias sem documento, com chamada direta para o upload.

## Fora de escopo

- Edição ou exclusão de documento pela interface.
- Visualizador de PDF embutido.

## Decisões técnicas

- **Método de extração exposto na interface.** Um documento vindo de OCR tem risco maior de
  erro; quem opera precisa saber disso ao avaliar uma prescrição.
- **Upload disparado a partir da lacuna.** O caminho natural é ver o que falta e resolver ali,
  não procurar um botão em outra tela.

## Contrato

```ts
GET  /api/documents -> Document[]
POST /api/documents (multipart: file, fault_family, title) -> { documentId, status, chunks }
```
