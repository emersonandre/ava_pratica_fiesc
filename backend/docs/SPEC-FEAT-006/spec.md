# SPEC-FEAT-006 — Extração de texto e OCR dos documentos

| | |
| --- | --- |
| **App** | backend |
| **Épico** | Similaridade e documentos |
| **Atende** | §3 — tratamento dos documentos fornecidos |
| **Depende de** | `SPEC-FEAT-001` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

Foram fornecidos 6 PDFs. **Doc2 a Doc6 têm camada de texto** e já foram identificados:
Doc2 = desalinhamento, Doc3 = desbalanceamento, Doc4 = correias, Doc5 = polias,
Doc6 = cocked rotor (rotor inclinado).

**Doc1.pdf é o caso difícil: 17 páginas e zero caractere extraível.** É um documento gerado
no Word com imagens coladas (metadado `/Creator: Microsoft® Word LTSC`). Ignorá-lo deixaria
um documento entregue pela empresa fora da solução.

## Escopo

- Detecção automática de camada de texto por documento (densidade de caracteres por página).
- Caminho A (texto): extração com `pypdf`.
- Caminho B (imagem): renderização das páginas com `pypdfium2` → OCR por modelo de visão →
  texto normalizado.
- Normalização comum: junção de hifenização, colapso de espaços, remoção de cabeçalho e
  rodapé repetidos, preservação dos títulos de seção numerados.
- Cada trecho carrega proveniência: `documento`, `página`, `método` (`text` | `ocr`) e,
  no OCR, um score de confiança.
- Cache em disco do OCR — reprocessar não repete chamadas pagas.

## Fora de escopo

- Interpretar figuras e diagramas técnicos além do texto neles contido.
- Tesseract local (não instalado na máquina; o modelo de visão dá qualidade melhor em
  português e não exige binário externo).

## Decisões técnicas

- **OCR por modelo de visão em vez de Tesseract.** Sem dependência de binário no Windows,
  melhor resultado em português e em texto dentro de imagem de baixo contraste.
- **OCR é etapa offline, de build.** Roda uma vez, resultado versionado em `artifacts/ocr/`.
  Nenhuma requisição do usuário dispara OCR — a restrição de §5 vale para a operação.
- **Proveniência obrigatória desde a extração.** Citação com página só é possível se o
  número da página for carregado desde o primeiro passo.

## Contrato

```python
@dataclass
class ExtractedPage:
    document: str
    page: int
    text: str
    method: Literal["text", "ocr"]
    confidence: float | None

def extract_document(path: Path) -> list[ExtractedPage]: ...
```
