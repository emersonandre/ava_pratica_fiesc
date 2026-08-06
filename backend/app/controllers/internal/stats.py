"""Estatisticas, cobertura e documentos -- consumidos pelo dashboard."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.controllers.v1.upload_doc import upload_doc
from app.core.taxonomy import (
    FAMILY_DESCRIPTIONS,
    PROBLEM_FAMILIES,
)
from app.database import get_session
from app.repositories import document as repo
from app.schemas.document import DocumentoOut, FamiliaOut, UploadDocResponse
from app.security import require_internal_key
from app.services import coverage

router = APIRouter(
    prefix="/api/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


class VisaoGeral(BaseModel):
    total_eventos: int
    eventos_problema: int
    familias: int
    familias_problema: int
    familias_cobertas: int
    familias_descobertas: list[str]
    documentos_indexados: int
    trechos_indexados: int
    periodo_inicio: date | None
    periodo_fim: date | None
    eventos_holdout: int
    ranking: list[FamiliaOut]


class PontoLinhaDoTempo(BaseModel):
    dia: date
    familia: str
    total: int


@router.get("/stats/overview", response_model=VisaoGeral)
def visao_geral(session: Annotated[Session, Depends(get_session)]) -> VisaoGeral:
    """KPIs do dashboard, em uma chamada so.

    A cobertura documental entra como indicador de primeira linha: e o diferencial
    conceitual da solucao -- o sistema sabe o que nao sabe.
    """
    geral = repo.visao_geral(session)
    contagens = repo.contagem_por_familia(session)
    mapa = coverage.mapa_de_cobertura(session)
    documentos = repo.listar_documentos(session)

    ranking = sorted(
        (
            FamiliaOut(
                familia=familia,
                descricao=FAMILY_DESCRIPTIONS.get(familia, ""),
                e_problema=familia in PROBLEM_FAMILIES,
                eventos=contagens.get(familia, 0),
                coberta=bool(mapa.get(familia)),
                documentos=[d.arquivo for d in mapa.get(familia, ())],
            )
            for familia in contagens
        ),
        key=lambda item: item.eventos,
        reverse=True,
    )

    descobertas = [f for f, docs in mapa.items() if not docs]

    return VisaoGeral(
        total_eventos=geral.total_eventos,
        eventos_problema=geral.eventos_problema,
        familias=geral.familias,
        familias_problema=len(PROBLEM_FAMILIES),
        familias_cobertas=len(PROBLEM_FAMILIES) - len(descobertas),
        familias_descobertas=sorted(descobertas),
        documentos_indexados=sum(1 for d, _ in documentos if d.status == "indexed"),
        trechos_indexados=sum(trechos for _, trechos in documentos),
        periodo_inicio=geral.periodo_inicio.date() if geral.periodo_inicio else None,
        periodo_fim=geral.periodo_fim.date() if geral.periodo_fim else None,
        eventos_holdout=geral.holdout,
        ranking=ranking,
    )


@router.get("/stats/timeline", response_model=list[PontoLinhaDoTempo])
def linha_do_tempo(
    session: Annotated[Session, Depends(get_session)],
    familia: Annotated[str | None, Query()] = None,
    desde: Annotated[date | None, Query()] = None,
) -> list[PontoLinhaDoTempo]:
    """Distribuicao temporal das ocorrencias, item pedido na secao 3 do enunciado."""
    return [
        PontoLinhaDoTempo(dia=linha.dia.date(), familia=linha.fault_family, total=linha.total)
        for linha in repo.linha_do_tempo(session, familia=familia, inicio=desde)
    ]


@router.get("/faults", response_model=list[FamiliaOut])
def familias(session: Annotated[Session, Depends(get_session)]) -> list[FamiliaOut]:
    """Familias canonicas com status de cobertura documental."""
    contagens = repo.contagem_por_familia(session)
    mapa = coverage.mapa_de_cobertura(session)

    return [
        FamiliaOut(
            familia=familia,
            descricao=FAMILY_DESCRIPTIONS.get(familia, ""),
            e_problema=familia in PROBLEM_FAMILIES,
            eventos=contagens.get(familia, 0),
            coberta=bool(mapa.get(familia)),
            documentos=[d.arquivo for d in mapa.get(familia, ())],
        )
        for familia in sorted(FAMILY_DESCRIPTIONS)
    ]


@router.post(
    "/documents",
    response_model=UploadDocResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_documento(
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File()],
    fault_family: Annotated[str, Form()],
    title: Annotated[str | None, Form()] = None,
) -> UploadDocResponse:
    """Upload pelo frontend.

    Mesma implementacao de `/api/v1/upload_doc`, com a autenticacao da superficie
    interna. O frontend usa chave estatica, nao JWT -- e nao teria como obter um
    token sem embutir a credencial de cliente no bundle.
    """
    return await upload_doc(session=session, file=file, fault_family=fault_family, title=title)


@router.get("/documents", response_model=list[DocumentoOut])
def documentos(session: Annotated[Session, Depends(get_session)]) -> list[DocumentoOut]:
    """Documentos indexados e estado da indexacao."""
    return [
        DocumentoOut(
            id=documento.id,
            arquivo=documento.filename,
            titulo=documento.title,
            familia=documento.fault_family,
            paginas=documento.pages,
            trechos=trechos,
            metodo=documento.extraction_method,
            confianca_ocr=(
                float(documento.ocr_confidence) if documento.ocr_confidence else None
            ),
            status=documento.status,
            erro=documento.error,
            criado_em=documento.created_at,
        )
        for documento, trechos in repo.listar_documentos(session)
    ]
