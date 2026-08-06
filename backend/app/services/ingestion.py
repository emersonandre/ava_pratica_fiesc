"""Ingestao de leituras vindas do chao de fabrica.

A secao 2 do enunciado descreve o fluxo: os sensores enviam leituras
continuamente para o banco corporativo, e o time de IA consome esse banco. Este
servico e a porta de entrada -- o `/predict` apenas consulta.

## O que acontece com uma leitura sem rotulo

O sensor mede o tempo todo; o operador anota depois, ou nunca. Uma leitura sem
`fault` e gravada assim mesmo, mas com `fault_family` nulo -- e o indice de
similaridade exclui esses registros. Nao ha condicao anotada para votar, entao
ela nao pode ser vizinha de ninguem.

Guardar em vez de recusar e deliberado: o dado do sensor e o que a empresa tem de
mais caro. Descartar a leitura porque falta a anotacao seria jogar fora a medicao
para preservar o rotulo.

## O que acontece com um rotulo desconhecido

Mesmo tratamento. Um rotulo fora da taxonomia -- uma condicao nova que ninguem
mapeou ainda -- grava a leitura como nao anotada e devolve o rotulo na resposta,
para que alguem decida se vale criar uma familia nova. A ingestao em lote nao
para por causa de um rotulo.

Isso difere da carga inicial (`scripts/ingest_csv`), que **aborta** em rotulo
desconhecido. La e um arquivo fechado, revisavel antes de rodar de novo; aqui e
um fluxo continuo que nao pode parar.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core import features as feat
from app.core.taxonomy import UnknownFaultLabel, normalize_fault
from app.models import SensorEvent
from app.schemas.ingest import IngestResponse, LeituraGravada, LeituraIn
from app.settings import get_settings

logger = logging.getLogger("prescritiva.ingestao")

SPLIT_PRODUCAO = "producao"


def _proximo_id(session: Session) -> int:
    """Id para leituras que chegam sem identificador do coletor."""
    maior = session.scalar(select(func.max(SensorEvent.id))) or 0
    return maior + 1


def ingerir(session: Session, leituras: list[LeituraIn]) -> IngestResponse:
    """Grava as leituras. Idempotente por id."""
    scaler = feat.load_scaler(get_settings().artifacts_path)

    ids_existentes = set()
    informados = [leitura.id for leitura in leituras if leitura.id is not None]
    if informados:
        ids_existentes = set(
            session.scalars(
                select(SensorEvent.id).where(SensorEvent.id.in_(informados))
            ).all()
        )

    proximo = _proximo_id(session)
    agora = datetime.now(UTC)

    registros: list[dict] = []
    resultado: list[LeituraGravada] = []
    desconhecidos: list[str] = []

    for leitura in leituras:
        identificador = leitura.id
        if identificador is None:
            identificador = proximo
            proximo += 1

        canonico = familia = None
        e_problema = None
        bruto = leitura.fault.strip() if leitura.fault else None

        if bruto:
            try:
                rotulo = normalize_fault(bruto)
                canonico, familia = rotulo.canonical, rotulo.family
                e_problema = rotulo.is_problem
            except UnknownFaultLabel:
                # Grava sem classificacao e reporta -- ver docstring do modulo.
                logger.warning("rotulo fora da taxonomia: %r", bruto)
                if bruto not in desconhecidos:
                    desconhecidos.append(bruto)

        metricas = leitura.metricas()
        vetor = feat.to_vector(scaler, metricas)

        registros.append(
            {
                "id": identificador,
                "created_at": leitura.created_at or agora,
                "raw_fault": bruto,
                "canonical_fault": canonico,
                "fault_family": familia,
                "is_problem": e_problema,
                "split": SPLIT_PRODUCAO,
                **metricas,
                "features": vetor.tolist(),
            }
        )

        resultado.append(
            LeituraGravada(
                id=identificador,
                condicao_bruta=bruto,
                condicao_canonica=canonico,
                familia=familia,
                e_problema=e_problema,
                anotada=familia is not None,
                ja_existia=identificador in ids_existentes,
            )
        )

    colunas = [chave for chave in registros[0] if chave != "id"]
    stmt = insert(SensorEvent).values(registros)
    # Reenviar a mesma leitura atualiza em vez de duplicar. O coletor pode
    # reenviar por falha de rede sem sujar a base -- e o operador pode anotar
    # depois uma leitura que chegou sem rotulo.
    stmt = stmt.on_conflict_do_update(
        index_elements=[SensorEvent.id],
        set_={coluna: stmt.excluded[coluna] for coluna in colunas},
    )
    session.execute(stmt)

    anotadas = sum(1 for item in resultado if item.anotada)
    atualizadas = sum(1 for item in resultado if item.ja_existia)

    logger.info(
        "ingestao: %d leituras, %d anotadas, %d atualizadas, %d rotulos desconhecidos",
        len(resultado),
        anotadas,
        atualizadas,
        len(desconhecidos),
    )

    return IngestResponse(
        gravadas=len(resultado),
        anotadas=anotadas,
        atualizadas=atualizadas,
        leituras=resultado,
        rotulos_desconhecidos=desconhecidos,
    )
