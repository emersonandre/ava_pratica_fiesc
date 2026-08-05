"""Indexacao de documentos: extrai, divide, embute e grava.

Mesmo pipeline para os documentos entregues pela empresa e para os que o usuario
registrar depois pela API (SPEC-FEAT-014). Um caminho so, sem codigo paralelo que
possa divergir.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.embeddings import embutir_documentos
from app.models import Document, DocumentChunk, FaultCoverage
from app.services.document_chunking import dividir
from app.services.document_extraction import DocumentoNaoProcessavel, extrair
from app.settings import get_settings

logger = logging.getLogger("prescritiva.indexacao")


class ResultadoIndexacao:
    def __init__(self, documento: Document, *, trechos: int, ja_existia: bool = False) -> None:
        self.documento = documento
        self.trechos = trechos
        self.ja_existia = ja_existia


def _buscar_por_hash(session: Session, hash_conteudo: str) -> Document | None:
    return session.scalars(
        select(Document).where(Document.content_hash == hash_conteudo)
    ).one_or_none()


def indexar(
    session: Session,
    caminho: Path,
    *,
    familia: str | None = None,
    titulo: str | None = None,
    forcar: bool = False,
) -> ResultadoIndexacao:
    """Indexa um documento. Idempotente por hash de conteudo."""
    documento = Document(
        filename=caminho.name,
        title=titulo or caminho.stem,
        fault_family=familia,
        pages=0,
        extraction_method="text",
        content_hash="",
        status="processing",
        created_at=datetime.now(UTC),
    )

    try:
        extraido = extrair(caminho)
    except DocumentoNaoProcessavel as erro:
        documento.status = "failed"
        documento.error = str(erro)
        documento.content_hash = f"falha:{caminho.name}"
        session.add(documento)
        session.flush()
        logger.error("indexacao de %s falhou: %s", caminho.name, erro)
        return ResultadoIndexacao(documento, trechos=0)

    existente = _buscar_por_hash(session, extraido.hash_conteudo)
    if existente and not forcar:
        logger.info("%s ja indexado (documento %d)", caminho.name, existente.id)
        return ResultadoIndexacao(existente, trechos=len(existente.chunks), ja_existia=True)
    if existente:
        # Reindexacao forcada: remove os trechos antigos para nao duplicar.
        session.delete(existente)
        session.flush()

    trechos = dividir(extraido.paginas)
    if not trechos:
        documento.status = "failed"
        documento.error = "nenhum trecho gerado"
        documento.content_hash = extraido.hash_conteudo
        session.add(documento)
        session.flush()
        return ResultadoIndexacao(documento, trechos=0)

    vetores = embutir_documentos([t.conteudo for t in trechos])

    documento.pages = len(extraido.paginas)
    documento.extraction_method = extraido.metodo
    documento.ocr_confidence = extraido.confianca_media
    documento.content_hash = extraido.hash_conteudo
    documento.status = "indexed"
    session.add(documento)
    session.flush()

    for trecho, vetor in zip(trechos, vetores, strict=True):
        session.add(
            DocumentChunk(
                document_id=documento.id,
                section=trecho.secao,
                page_start=trecho.pagina_inicial,
                page_end=trecho.pagina_final,
                ordinal=trecho.ordinal,
                content=trecho.conteudo,
                embedding=vetor.tolist(),
            )
        )

    if familia:
        vincular_cobertura(session, familia, documento, origem="upload")

    session.flush()
    logger.info(
        "%s indexado: %d paginas, %d trechos, metodo=%s",
        caminho.name,
        documento.pages,
        len(trechos),
        extraido.metodo,
    )
    return ResultadoIndexacao(documento, trechos=len(trechos))


def vincular_cobertura(
    session: Session,
    familia: str,
    documento: Document,
    *,
    origem: str = "manual",
    evidencia: str | None = None,
) -> FaultCoverage:
    """Liga uma familia de falha ao documento que a cobre.

    O vinculo e explicito e revisado -- nunca inferido pelo LLM. E o que sustenta
    a regra da secao 3 do enunciado: sem linha aqui, o modelo nao e chamado.
    """
    existente = session.scalars(
        select(FaultCoverage).where(
            FaultCoverage.fault_family == familia,
            FaultCoverage.document_id == documento.id,
        )
    ).one_or_none()
    if existente:
        return existente

    cobertura = FaultCoverage(
        fault_family=familia,
        document_id=documento.id,
        source=origem,
        evidence=evidencia,
    )
    session.add(cobertura)
    session.flush()
    return cobertura


def registrar_metadado_do_indice(session: Session) -> None:
    """Grava modelo e dimensao usados, para detectar troca sem reindexacao."""
    from app.models import IndexMetadata

    settings = get_settings()
    agora = datetime.now(UTC)
    for chave, valor in (
        ("embedding_model", settings.embedding_model),
        ("embedding_dim", str(settings.embedding_dim)),
    ):
        registro = session.get(IndexMetadata, chave)
        if registro is None:
            session.add(IndexMetadata(key=chave, value=valor, updated_at=agora))
        else:
            registro.value = valor
            registro.updated_at = agora
    session.flush()
