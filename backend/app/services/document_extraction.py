"""Extracao de texto dos documentos tecnicos.

Dois caminhos, escolhidos por deteccao automatica:

- **camada de texto** (Doc2 a Doc6): extracao direta com `pypdf`.
- **paginas em imagem** (Doc1): renderizacao com `pypdfium2` e OCR local em ONNX.

O Doc1 tem 17 paginas e zero caractere extraivel -- e um documento do Word com
prints colados (`/Creator: Microsoft Word LTSC`). Ignora-lo custaria caro: o OCR
revelou que ele e justamente o **procedimento de rolamentos**, a familia com
60.779 registros, 36% de toda a base.

O OCR e etapa **offline, de build**: roda uma vez e o resultado fica em cache no
disco. Nenhuma requisicao de usuario dispara transcricao.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pypdf import PdfReader

from app.integrations import ocr as motor_ocr
from app.settings import get_settings

logger = logging.getLogger("prescritiva.documentos")

Metodo = Literal["text", "ocr"]

# Abaixo disso a pagina e considerada sem camada de texto util. Uma pagina de
# procedimento tecnico tem centenas de caracteres; 40 e folgado o suficiente para
# nao classificar como imagem uma pagina de rosto legitima.
MINIMO_CARACTERES_POR_PAGINA = 40

# Paginas abaixo desta confianca media entram no relatorio de revisao humana.
CONFIANCA_MINIMA_PAGINA = 0.75


class DocumentoNaoProcessavel(RuntimeError):
    """O documento existe mas nao pode ser transformado em texto agora."""


@dataclass(slots=True)
class PaginaExtraida:
    documento: str
    pagina: int
    texto: str
    metodo: Metodo
    confianca: float | None = None


@dataclass(slots=True)
class DocumentoExtraido:
    caminho: Path
    paginas: list[PaginaExtraida]
    metodo: Metodo
    hash_conteudo: str

    @property
    def texto(self) -> str:
        return "\n\n".join(p.texto for p in self.paginas if p.texto.strip())

    @property
    def confianca_media(self) -> float | None:
        valores = [p.confianca for p in self.paginas if p.confianca is not None]
        return sum(valores) / len(valores) if valores else None


# --- normalizacao ---------------------------------------------------------

_HIFENIZACAO = re.compile(r"(\w)-\s*\n\s*(\w)")
_ESPACOS = re.compile(r"[ \t]+")
_LINHAS_VAZIAS = re.compile(r"\n{3,}")


def normalizar(texto: str) -> str:
    """Junta hifenizacao de quebra de linha e colapsa espacos.

    Os titulos de secao numerados sao preservados de proposito: sao as fronteiras
    de chunk usadas na indexacao.
    """
    texto = texto.replace("\r\n", "\n").replace("\xa0", " ")
    texto = _HIFENIZACAO.sub(r"\1\2", texto)
    texto = _ESPACOS.sub(" ", texto)
    texto = "\n".join(linha.strip() for linha in texto.split("\n"))
    return _LINHAS_VAZIAS.sub("\n\n", texto).strip()


def hash_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


# --- deteccao -------------------------------------------------------------


def tem_camada_de_texto(caminho: Path) -> bool:
    leitor = PdfReader(caminho)
    for pagina in leitor.pages:
        if len((pagina.extract_text() or "").strip()) >= MINIMO_CARACTERES_POR_PAGINA:
            return True
    return False


# --- caminho A: camada de texto -------------------------------------------


def _extrair_texto(caminho: Path) -> list[PaginaExtraida]:
    leitor = PdfReader(caminho)
    paginas = []
    for numero, pagina in enumerate(leitor.pages, start=1):
        texto = normalizar(pagina.extract_text() or "")
        if texto:
            paginas.append(
                PaginaExtraida(documento=caminho.name, pagina=numero, texto=texto, metodo="text")
            )
    return paginas


# --- caminho B: OCR local -------------------------------------------------


def _arquivo_cache(caminho: Path) -> Path:
    diretorio = get_settings().artifacts_path / "ocr"
    diretorio.mkdir(parents=True, exist_ok=True)
    # A chave inclui o hash do arquivo: editar o PDF invalida o cache sozinho.
    return diretorio / f"{caminho.stem}_{hash_arquivo(caminho)[:16]}.json"


def _extrair_ocr(caminho: Path) -> list[PaginaExtraida]:
    cache = _arquivo_cache(caminho)

    if cache.exists():
        dados = json.loads(cache.read_text(encoding="utf-8"))
        logger.info("ocr %s: %d paginas do cache", caminho.name, len(dados))
    else:
        try:
            paginas_ocr = motor_ocr.transcrever_pdf(caminho)
        except motor_ocr.OCRIndisponivel as erro:
            raise DocumentoNaoProcessavel(str(erro)) from erro
        dados = [
            {
                "pagina": p.pagina,
                "texto": p.texto,
                "confianca": p.confianca,
                "blocos": p.blocos,
                "blocos_duvidosos": p.blocos_duvidosos,
            }
            for p in paginas_ocr
        ]
        cache.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    paginas: list[PaginaExtraida] = []
    for item in dados:
        texto = normalizar(item["texto"])
        if not texto:
            continue
        if item["confianca"] < CONFIANCA_MINIMA_PAGINA:
            logger.warning(
                "%s p%d com confianca %.3f -- candidata a revisao humana",
                caminho.name,
                item["pagina"],
                item["confianca"],
            )
        paginas.append(
            PaginaExtraida(
                documento=caminho.name,
                pagina=item["pagina"],
                texto=texto,
                confianca=item["confianca"],
                metodo="ocr",
            )
        )
    return paginas


# --- fachada --------------------------------------------------------------


def extrair(caminho: Path) -> DocumentoExtraido:
    """Extrai o texto de um documento, escolhendo o caminho automaticamente."""
    if not caminho.exists():
        raise DocumentoNaoProcessavel(f"{caminho} nao encontrado.")

    if tem_camada_de_texto(caminho):
        paginas = _extrair_texto(caminho)
        metodo: Metodo = "text"
    else:
        logger.info("%s sem camada de texto -- indo para OCR", caminho.name)
        paginas = _extrair_ocr(caminho)
        metodo = "ocr"

    if not paginas:
        raise DocumentoNaoProcessavel(f"{caminho.name} nao produziu texto utilizavel.")

    return DocumentoExtraido(
        caminho=caminho,
        paginas=paginas,
        metodo=metodo,
        hash_conteudo=hash_arquivo(caminho),
    )
