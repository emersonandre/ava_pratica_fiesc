"""Consultas sobre a base documental e as estatisticas do dashboard."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk, SensorEvent


def listar_documentos(session: Session) -> list[Row]:
    trechos = (
        select(
            DocumentChunk.document_id.label("document_id"),
            func.count().label("trechos"),
        )
        .group_by(DocumentChunk.document_id)
        .subquery()
    )
    return session.execute(
        select(Document, func.coalesce(trechos.c.trechos, 0).label("trechos"))
        .outerjoin(trechos, trechos.c.document_id == Document.id)
        .order_by(Document.filename)
    ).all()


def contagem_por_familia(session: Session) -> dict[str, int]:
    linhas = session.execute(
        select(SensorEvent.fault_family, func.count()).group_by(SensorEvent.fault_family)
    ).all()
    return {familia: total for familia, total in linhas}


def contagem_holdout_por_familia(session: Session) -> dict[str, int]:
    """Leituras disponiveis no conjunto de teste, por familia.

    Nem toda familia aparece la: `ventoinha`, por exemplo, tem 12.299 leituras no
    historico e nenhuma no periodo reservado para avaliacao. A interface precisa
    saber disso para nao oferecer uma condicao que nao tem o que demonstrar.
    """
    linhas = session.execute(
        select(SensorEvent.fault_family, func.count())
        .where(SensorEvent.split == "holdout")
        .group_by(SensorEvent.fault_family)
    ).all()
    return {familia: total for familia, total in linhas}


def visao_geral(session: Session) -> Row:
    return session.execute(
        select(
            func.count().label("total_eventos"),
            func.count().filter(SensorEvent.is_problem).label("eventos_problema"),
            func.count(func.distinct(SensorEvent.fault_family)).label("familias"),
            func.min(SensorEvent.created_at).label("periodo_inicio"),
            func.max(SensorEvent.created_at).label("periodo_fim"),
            func.count().filter(SensorEvent.split == "holdout").label("holdout"),
        ).select_from(SensorEvent)
    ).one()


def linha_do_tempo(
    session: Session, *, familia: str | None = None, inicio: date | None = None
) -> list[Row]:
    dia = func.date_trunc("day", SensorEvent.created_at).label("dia")
    consulta = select(dia, SensorEvent.fault_family, func.count().label("total"))
    if familia:
        consulta = consulta.where(SensorEvent.fault_family == familia)
    if inicio:
        consulta = consulta.where(SensorEvent.created_at >= inicio)
    return session.execute(
        consulta.group_by(dia, SensorEvent.fault_family).order_by(dia)
    ).all()
