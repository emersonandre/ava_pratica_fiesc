"""Consultas sobre `sensor_events`.

Toda consulta ao banco relacionada a eventos de sensor vive aqui. Servicos
recebem dados prontos; nao montam SQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Row, func, select, text
from sqlalchemy.orm import Session

from app.models import SensorEvent

# Toda busca por similaridade e restrita ao historico anotado.
#
# Fora ficam o holdout (buscar la seria vazamento) e as leituras sem rotulo
# (nao ha condicao anotada para votar). O indice HNSW e parcial exatamente sobre
# este filtro -- se a condicao aqui mudar, o indice precisa mudar junto, senao o
# pos-filtro do pgvector volta a devolver resultado vazio.
SPLIT_HOLDOUT = "holdout"
SPLIT_PRODUCAO = "producao"



@dataclass(frozen=True, slots=True)
class Vizinho:
    id: int
    created_at: datetime
    canonical_fault: str
    fault_family: str
    is_problem: bool
    rpm: float
    temperature_c: float
    distance: float

    @property
    def similarity(self) -> float:
        """Similaridade cosseno em [0, 1]."""
        return 1.0 - self.distance


def buscar_vizinhos(
    session: Session, vetor: list[float], *, k: int, excluir_id: int | None = None
) -> list[Vizinho]:
    """k vizinhos mais proximos no historico, por distancia cosseno."""
    # `hnsw.ef_search` limita quantos candidatos o indice examina; o padrao e 40.
    # Pedir k=50 com ef_search=40 devolve menos de 50 linhas em silencio -- foi
    # exatamente o que aconteceu no primeiro teste (41 de 50). Alem disso, um
    # ef_search folgado melhora o recall da busca aproximada.
    #
    # `SET LOCAL` nao aceita parametro vinculado no PostgreSQL; `set_config` aceita.
    # O terceiro argumento (true) limita o efeito a transacao corrente.
    session.execute(
        text("SELECT set_config('hnsw.ef_search', :ef, true)"),
        {"ef": str(max(64, k * 4))},
    )

    distancia = SensorEvent.features.cosine_distance(vetor).label("distancia")

    linhas = session.execute(
        select(
            SensorEvent.id,
            SensorEvent.created_at,
            SensorEvent.canonical_fault,
            SensorEvent.fault_family,
            SensorEvent.is_problem,
            SensorEvent.rpm,
            SensorEvent.temperature_c,
            distancia,
        )
        .where(
            SensorEvent.split != SPLIT_HOLDOUT,
            SensorEvent.fault_family.is_not(None),
            # Uma leitura recem-ingerida nao pode ser vizinha de si mesma: o vetor
            # consultado e o dela, entao apareceria com similaridade 1,0 e
            # dominaria a votacao.
            SensorEvent.id != excluir_id if excluir_id is not None else text("true"),
        )
        .order_by(distancia)
        .limit(k)
    ).all()

    return [
        Vizinho(
            id=linha.id,
            created_at=linha.created_at,
            canonical_fault=linha.canonical_fault,
            fault_family=linha.fault_family,
            is_problem=linha.is_problem,
            rpm=float(linha.rpm),
            temperature_c=float(linha.temperature_c),
            distance=float(linha.distancia),
        )
        for linha in linhas
    ]


def serie_temporal(session: Session, familia: str) -> list[Row]:
    """Ocorrencias por dia da familia no historico."""
    dia = func.date_trunc("day", SensorEvent.created_at).label("dia")
    return session.execute(
        select(dia, func.count().label("total"))
        .where(
            SensorEvent.split != SPLIT_HOLDOUT,
            SensorEvent.fault_family == familia,
        )
        .group_by(dia)
        .order_by(dia)
    ).all()


def estatisticas_familia(session: Session, familia: str) -> Row | None:
    """Total, periodo e faixas operacionais da familia no historico."""
    return session.execute(
        select(
            func.count().label("total"),
            func.min(SensorEvent.created_at).label("primeiro"),
            func.max(SensorEvent.created_at).label("ultimo"),
            func.min(SensorEvent.rpm).label("rpm_min"),
            func.max(SensorEvent.rpm).label("rpm_max"),
            func.avg(SensorEvent.rpm).label("rpm_medio"),
            func.min(SensorEvent.temperature_c).label("temp_min"),
            func.max(SensorEvent.temperature_c).label("temp_max"),
            func.avg(SensorEvent.temperature_c).label("temp_media"),
        ).where(
            SensorEvent.split != SPLIT_HOLDOUT,
            SensorEvent.fault_family == familia,
        )
    ).one_or_none()


def familias_com_historico(session: Session) -> set[str]:
    """Familias presentes no historico.

    Uma familia ausente daqui nunca pode ser diagnosticada por similaridade --
    e o caso de `falta_fase`, que so aparece no holdout.
    """
    return set(
        session.scalars(
            select(SensorEvent.fault_family)
            .where(SensorEvent.split != SPLIT_HOLDOUT, SensorEvent.fault_family.is_not(None))
            .distinct()
        ).all()
    )


def amostra_holdout(session: Session, *, familia: str | None = None) -> SensorEvent | None:
    """Um evento aleatorio do holdout, para demonstracao com dado nao visto."""
    consulta = select(SensorEvent).where(SensorEvent.split == "holdout")
    if familia:
        consulta = consulta.where(SensorEvent.fault_family == familia)
    return session.scalars(consulta.order_by(text("random()")).limit(1)).one_or_none()


def candidatos_holdout(
    session: Session, *, familia: str | None = None, limite: int = 250
) -> list[SensorEvent]:
    """Varios eventos do holdout, para procurar um que produza certo desfecho.

    Sobre o holdout o sistema se abstem em cerca de dois tercos dos casos -- e o
    resultado honesto, dado o deslocamento de distribuicao. Numa demonstracao,
    porem, sortear as cegas esconde metade do comportamento: quem assiste ve
    varias recusas seguidas e nao consegue distinguir "funcionando como
    projetado" de "quebrado".
    """
    consulta = select(SensorEvent).where(SensorEvent.split == "holdout")
    if familia:
        consulta = consulta.where(SensorEvent.fault_family == familia)
    return list(session.scalars(consulta.order_by(text("random()")).limit(limite)).all())
