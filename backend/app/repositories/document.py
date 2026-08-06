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


def distribuicao_por_familia(session: Session, *, metrica: str) -> list[Row]:
    """Quartis de uma metrica em cada familia.

    Percentil e nao media: as distribuicoes sao assimetricas -- algumas leituras
    de rolamento tem pico de aceleracao dez vezes acima da mediana, e a media
    sozinha esconderia isso.

    E o grafico que explica a acuracia do sistema. Onde as faixas de duas
    familias se sobrepoem, nenhuma busca por vizinho consegue separa-las; a
    limitacao esta no sensor, nao no metodo.
    """
    coluna = getattr(SensorEvent, metrica)
    return session.execute(
        select(
            SensorEvent.fault_family,
            func.count().label("leituras"),
            func.percentile_cont(0.10).within_group(coluna).label("p10"),
            func.percentile_cont(0.25).within_group(coluna).label("p25"),
            func.percentile_cont(0.50).within_group(coluna).label("mediana"),
            func.percentile_cont(0.75).within_group(coluna).label("p75"),
            func.percentile_cont(0.90).within_group(coluna).label("p90"),
        )
        .where(SensorEvent.fault_family.is_not(None), coluna.is_not(None))
        .group_by(SensorEvent.fault_family)
        .order_by(func.percentile_cont(0.50).within_group(coluna).desc())
    ).all()


def frequencia_por_familia(session: Session) -> list[Row]:
    """Com que frequencia cada falha aparece -- item pedido na secao 1.

    A unidade de contagem e o DIA, nao a leitura. O coletor amostra a cada poucos
    segundos durante uma sessao de ensaio, entao intervalo entre leituras mede a
    cadencia do equipamento e nao a recorrencia do defeito -- daria "uma falha de
    rolamento a cada 36 segundos", que e absurdo.

    Dias distintos com ocorrencia e a aproximacao honesta de "quantas vezes o
    problema apareceu" nesta base.
    """
    return session.execute(
        select(
            SensorEvent.fault_family,
            func.count().label("leituras"),
            func.min(SensorEvent.created_at).label("primeira"),
            func.max(SensorEvent.created_at).label("ultima"),
            func.count(func.distinct(func.date_trunc("day", SensorEvent.created_at))).label(
                "dias_com_ocorrencia"
            ),
        )
        .where(SensorEvent.fault_family.is_not(None))
        .group_by(SensorEvent.fault_family)
        .order_by(func.count().desc())
    ).all()
