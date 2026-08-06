"""POST /api/v1/upload_doc -- registro de novo documento orientativo.

Fecha o ciclo que a secao 3 do enunciado pede: o sistema recusa por falta de
documentacao **e sugere registrar um documento**. Depois do upload, a mesma
pergunta passa a ser respondida com citacao.

O pipeline de indexacao e o mesmo dos documentos entregues pela empresa
(`services/document_indexing`), incluindo OCR automatico para PDF sem camada de
texto. Um caminho so, sem codigo paralelo que possa divergir.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.taxonomy import FAMILY_DESCRIPTIONS, PROBLEM_FAMILIES
from app.database import get_session
from app.schemas.document import UploadDocResponse
from app.security import require_scope
from app.services.document_indexing import indexar

logger = logging.getLogger("prescritiva.api")

router = APIRouter(prefix="/api/v1", tags=["v1"])

TAMANHO_MAXIMO = 20 * 1024 * 1024  # 20 MB
ASSINATURA_PDF = b"%PDF-"


@router.post(
    "/upload_doc",
    response_model=UploadDocResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("upload"))],
    summary="Registra um documento orientativo e injeta no banco vetorial",
)
async def upload_doc(
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File(description="PDF do procedimento")],
    fault_family: Annotated[str, Form(description="Familia de falha que o documento cobre")],
    title: Annotated[str | None, Form()] = None,
) -> UploadDocResponse:
    """Envia um documento, processa e vincula a uma familia de falha.

    A familia e **informada por quem registra**, nao inferida pelo modelo. Quem
    cadastra sabe a que defeito o documento se refere; inferir introduziria erro
    justamente no mecanismo que sustenta a regra antialucinacao.
    """
    if fault_family not in PROBLEM_FAMILIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Familia de falha desconhecida: {fault_family!r}. "
                f"Valores aceitos: {sorted(PROBLEM_FAMILIES)}."
            ),
        )

    conteudo = await file.read()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio."
        )
    if len(conteudo) > TAMANHO_MAXIMO:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo acima de {TAMANHO_MAXIMO // (1024 * 1024)} MB.",
        )
    # Confia na assinatura do arquivo, nao na extensao nem no content-type: os
    # dois vem do cliente e podem mentir.
    if not conteudo.startswith(ASSINATURA_PDF):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo enviado nao e um PDF valido.",
        )

    nome = Path(file.filename or "documento.pdf").name
    with tempfile.TemporaryDirectory() as diretorio:
        caminho = Path(diretorio) / nome
        caminho.write_bytes(conteudo)

        resultado = indexar(
            session,
            caminho,
            familia=fault_family,
            titulo=title or Path(nome).stem,
        )

    documento = resultado.documento

    if documento.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Nao foi possivel processar o documento: {documento.error}",
        )

    logger.info(
        "documento registrado id=%d familia=%s trechos=%d metodo=%s",
        documento.id,
        fault_family,
        resultado.trechos,
        documento.extraction_method,
    )

    return UploadDocResponse(
        document_id=documento.id,
        status=documento.status,
        arquivo=documento.filename,
        titulo=documento.title,
        familia=fault_family,
        familia_descricao=FAMILY_DESCRIPTIONS.get(fault_family, ""),
        paginas=documento.pages,
        trechos=resultado.trechos,
        metodo=documento.extraction_method,
        confianca_ocr=(
            float(documento.ocr_confidence) if documento.ocr_confidence else None
        ),
        ja_existia=resultado.ja_existia,
        cobertura_atualizada=resultado.cobertura_nova or not resultado.ja_existia,
    )
