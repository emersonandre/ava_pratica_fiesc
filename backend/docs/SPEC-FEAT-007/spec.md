# SPEC-FEAT-007 — Indexação semântica dos documentos

| | |
| --- | --- |
| **App** | backend |
| **Épico** | Similaridade e documentos |
| **Atende** | §3 — integrar-se à base documental; §5 — executar em estação de trabalho |
| **Depende de** | `SPEC-FEAT-006` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

Os procedimentos seguem estrutura regular ("1. Objetivo", "3. Sintomas Comuns",
"5. Procedimento de Correção", "Validação"). Essa estrutura é uma dádiva para o chunking:
as fronteiras de seção são fronteiras semânticas reais, muito melhores que cortar a cada N
caracteres no meio de um passo de procedimento.

## Escopo

- Chunking guiado por seção, com limite de tamanho e sobreposição para seções longas.
- Cada chunk guarda: documento, páginas cobertas, título da seção, posição e texto.
- Embeddings **locais** via `fastembed` (ONNX Runtime, modelo multilíngue) — sem rede,
  sem GPU, coerente com a restrição de §5.
- Persistência em `document_chunks` com índice HNSW.
- Metadado do índice (nome do modelo e dimensão) gravado; troca de modelo exige reindexação
  explícita em vez de corromper o índice.

## Fora de escopo

- Embeddings por API. Manter local reforça a restrição de operação e elimina custo por consulta.
- Reranker dedicado (cross-encoder) — o filtro por família da SPEC-FEAT-010 já elimina a
  maior fonte de ruído.

## Decisões técnicas

- **Chunking por seção, não por janela fixa.** Um procedimento cortado ao meio gera resposta
  prescritiva incompleta — exatamente o erro mais caro nesta aplicação.
- **`fastembed`/ONNX em vez de `sentence-transformers`/PyTorch.** Dependência de ~50 MB em vez
  de ~2,5 GB, roda em CPU, e sustenta melhor a narrativa de "opera na workstation".
- **Modelo multilíngue.** Documentos e perguntas dos operadores são em português.

## Contrato

```sql
CREATE TABLE document_chunks (
    id            SERIAL PRIMARY KEY,
    document_id   INT REFERENCES documents(id) ON DELETE CASCADE,
    section       TEXT,
    page_start    INT NOT NULL,
    page_end      INT NOT NULL,
    ordinal       INT NOT NULL,
    content       TEXT NOT NULL,
    embedding     VECTOR(384) NOT NULL
);
```
