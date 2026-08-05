"""OCR local, offline.

`rapidocr-onnxruntime` roda PP-OCR em ONNX Runtime na CPU. Mesma escolha do
`fastembed`: instala por pip, sem binario de sistema, sem GPU e sem chamada de
rede. Reforca a restricao da secao 5 do enunciado -- a solucao opera em estacao de
trabalho comercial -- e nao amarra a preparacao da base a credito de API.

Alternativas descartadas, com o motivo:

- **Modelo de visao por API** (plano original): DeepSeek nao aceita imagem em
  nenhum modelo (`v4-flash`, `v4-pro`, `chat`, `vl2` -- todos testados), e a conta
  OpenAI disponivel estava sem credito. Amarrar a indexacao a credito externo
  tambem contraria o espirito da restricao de operacao.
- **Tesseract**: exigiria instalacao de binario no sistema.

Limitacao conhecida: o modelo transcreve texto latino mas **perde diacriticos**
("Diagnostico" no lugar de "Diagnóstico"). Nao inviabiliza a recuperacao -- o
modelo de embedding e multilingue e tolera a variacao -- mas o texto extraido nao
e fiel ao original nesse aspecto, e por isso os documentos vindos de OCR ficam
sinalizados na interface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

logger = logging.getLogger("prescritiva.ocr")

# 3x da ~220 dpi. Abaixo disso a taxa de acerto cai visivelmente em texto de
# corpo; acima, o ganho nao compensa o tempo de processamento.
ESCALA_RENDER = 3.0

# Blocos abaixo deste nivel entram no relatorio de revisao em vez de serem
# aceitos em silencio.
CONFIANCA_MINIMA_BLOCO = 0.60


class OCRIndisponivel(RuntimeError):
    """Motor de OCR nao instalado."""


@dataclass(slots=True)
class PaginaOCR:
    pagina: int
    texto: str
    confianca: float
    blocos: int
    blocos_duvidosos: int


@lru_cache
def _motor():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as erro:  # pragma: no cover
        raise OCRIndisponivel(
            "rapidocr-onnxruntime nao instalado. Rode: pip install rapidocr-onnxruntime"
        ) from erro
    logger.info("carregando motor de OCR (ONNX, CPU)")
    return RapidOCR()


def transcrever_pdf(caminho: Path) -> list[PaginaOCR]:
    """Renderiza cada pagina e transcreve. Documento inteiro, em memoria por pagina."""
    import pypdfium2 as pdfium

    motor = _motor()
    documento = pdfium.PdfDocument(caminho)
    paginas: list[PaginaOCR] = []

    try:
        for indice in range(len(documento)):
            imagem = documento[indice].render(scale=ESCALA_RENDER).to_pil()
            resultado, _ = motor(np.array(imagem))

            if not resultado:
                logger.warning("%s p%d sem texto reconhecido", caminho.name, indice + 1)
                continue

            # Cada item e [caixa, texto, confianca]; a confianca vem como string.
            textos = [linha[1] for linha in resultado]
            confiancas = [float(linha[2]) for linha in resultado]

            paginas.append(
                PaginaOCR(
                    pagina=indice + 1,
                    texto="\n".join(textos),
                    confianca=sum(confiancas) / len(confiancas),
                    blocos=len(resultado),
                    blocos_duvidosos=sum(1 for c in confiancas if c < CONFIANCA_MINIMA_BLOCO),
                )
            )
            logger.info(
                "ocr %s p%d/%d  %d blocos  confianca %.3f",
                caminho.name,
                indice + 1,
                len(documento),
                len(resultado),
                paginas[-1].confianca,
            )
    finally:
        documento.close()

    return paginas
