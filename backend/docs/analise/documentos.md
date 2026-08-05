# Base documental

> Gerado por `python manage.py report documentos`.
> Evidencia das [SPEC-FEAT-006](../SPEC-FEAT-006/spec.md) e [SPEC-FEAT-007](../SPEC-FEAT-007/spec.md).

## Documentos indexados

| Arquivo | Titulo | Familia | Paginas | Trechos | Extracao | Confianca |
| --- | --- | --- | ---: | ---: | --- | ---: |
| `Doc1.pdf` | Procedimento para Diagnostico e Correcao de Problemas em Rolamentos | `rolamento` | 17 | 26 | ocr | 0.881 |
| `Doc2.pdf` | Procedimento para Correcao de Desalinhamento em Motor Eletrico | `desalinhamento` | 6 | 16 | text | — |
| `Doc3.pdf` | Procedimento para Correcao de Desbalanceamento em Maquinas Rotativas | `desbalanceamento` | 10 | 18 | text | — |
| `Doc4.pdf` | Procedimento para Diagnostico e Correcao de Problemas em Correias | `correia` | 9 | 21 | text | — |
| `Doc5.pdf` | Procedimento para Diagnostico e Correcao de Problemas em Polias | `polia` | 10 | 22 | text | — |
| `Doc6.pdf` | Procedimento para Diagnostico e Correcao de Rotor Inclinado (Cocked Rotor) | `cocked_rotor` | 10 | 21 | text | — |

**Total: 6 documentos, 124 trechos indexados.**

## O caso do Doc1

O `Doc1.pdf` tem 17 paginas e **zero caractere extraivel** — e um documento do Word com prints colados (`/Creator: Microsoft Word LTSC`). A deteccao automatica de camada de texto o encaminha para o OCR.

O resultado justificou o esforco: **o Doc1 e o procedimento de rolamentos**, a familia com 60.779 registros, 36% de toda a base. Suas secoes 4.1 a 4.4 tratam de defeito na pista externa, pista interna, esferas e combinado — exatamente os rotulos canonicos `rolamento_outer`, `rolamento_inner`, `rolamento_ball` e `rolamento_combination`. Sem OCR, a maior massa do dataset ficaria sem documentacao.

### Motor de OCR

`rapidocr-onnxruntime` (PP-OCR em ONNX Runtime), local, CPU, offline. Alternativas descartadas com o motivo registrado:

| Alternativa | Por que nao |
| --- | --- |
| Modelo de visao por API (plano original) | Nenhum modelo DeepSeek aceita imagem — `v4-flash`, `v4-pro`, `chat` e `vl2` foram testados. A conta OpenAI disponivel estava sem credito. Amarrar a preparacao da base a credito externo tambem contraria a restricao de operacao da secao 5 |
| Tesseract | Exigiria instalacao de binario no sistema |

### Limitacao conhecida do OCR

O modelo transcreve texto latino mas **perde diacriticos** e confunde caracteres de forma parecida. Exemplos reais do Doc1:

| Transcrito | Original |
| --- | --- |
| `Diagnostico` | Diagnóstico |
| `lnner Race Fault` | Inner Race Fault |
| `guando` | quando |

Isso nao inviabiliza a recuperacao — o modelo de embedding e multilingue e tolera a variacao, e as sondas do Doc1 acertam. Mas o texto nao e fiel ao original, e por isso os documentos vindos de OCR ficam **sinalizados** no campo `extraction_method` e devem aparecer marcados na interface: uma prescricao baseada em OCR carrega mais risco que uma baseada em camada de texto.

## Chunking

A divisao segue os cabecalhos numerados dos procedimentos (`1. Objetivo`, `4.1. Correia Frouxa`, `3.1. Excentricidade`), que sao fronteiras semanticas reais. Cortar a cada N caracteres quebraria um procedimento no meio — e meio procedimento de manutencao e a falha mais cara possivel nesta aplicacao: o tecnico recebe metade dos passos de uma intervencao fisica em equipamento.

Embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensoes), local em ONNX Runtime, CPU, sem chamada de rede.
