"""Motor de similaridade historica.

Dado um evento novo, encontra os registros historicos de comportamento semelhante
e devolve o contexto que a secao 3 do enunciado pede: quantos eventos parecidos ja
ocorreram, como se distribuem no tempo, com que frequencia e em que condicao
operacional.

## Por que voto ponderado e nao maioria simples

Com `k` fixo, vizinhos distantes votariam com o mesmo peso dos proximos. O peso
e a similaridade cosseno.

## Por que a confianca vem da CONCORDANCIA e nao da distancia

Medicao sobre 3.000 eventos do holdout (docs/analise/similaridade.md):

    portao por concordancia    limiar 0,70 -> 50% de cobertura, 54% de precisao
                               limiar 0,95 -> 23% de cobertura, 71% de precisao
    portao por distancia       distancia <= 0,5 -> 13% de cobertura, 18% de precisao

A distancia e **anticorrelacionada** com o acerto: os vizinhos mais proximos caem
no cluster dominante de `rolamento` (36% do historico), entao proximidade alta
frequentemente significa "foi absorvido pela classe majoritaria". Usar distancia
como sinal de confianca, que era o plano inicial, teria produzido exatamente o
comportamento errado -- alta confianca nos casos mais enviesados.

## Por que o sistema se abstem tanto

O holdout tem deslocamento de distribuicao real em relacao ao historico. Um
classificador supervisionado (gradient boosting) atinge 39,8% no holdout contra
78,8% no proprio treino -- ou seja, o teto nao e do metodo, e dos dados. Em
manutencao industrial, prescrever intervencao fisica com 40% de acerto e pior que
admitir desconhecimento. A abstencao e o comportamento correto, nao uma falha.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.taxonomy import STATE_FAMILIES
from app.repositories import sensor_event as repo
from app.schemas.similarity import (
    ContextoOperacional,
    Evidencia,
    PontoTemporal,
    SimilarityResult,
    VotoFamilia,
)
from app.schemas.similarity import Vizinho as VizinhoSchema
from app.settings import get_settings


def _votar(vizinhos: list[repo.Vizinho]) -> tuple[list[VotoFamilia], float, str]:
    """Voto ponderado pela similaridade. Devolve votos, confianca e familia vencedora."""
    pesos: dict[str, float] = defaultdict(float)
    contagem: Counter[str] = Counter()

    for vizinho in vizinhos:
        # Similaridade cosseno como peso: vizinho distante pesa menos.
        pesos[vizinho.fault_family] += max(vizinho.similarity, 0.0)
        contagem[vizinho.fault_family] += 1

    total = sum(pesos.values()) or 1.0
    votos = sorted(
        (
            VotoFamilia(
                fault_family=familia,
                vizinhos=contagem[familia],
                peso=peso / total,
            )
            for familia, peso in pesos.items()
        ),
        key=lambda voto: voto.peso,
        reverse=True,
    )
    return votos, votos[0].peso, votos[0].fault_family


def _montar_evidencia(
    session: Session, familia: str, vizinhos: list[repo.Vizinho]
) -> Evidencia | None:
    estatisticas = repo.estatisticas_familia(session, familia)
    if estatisticas is None or not estatisticas.total:
        return None

    serie = repo.serie_temporal(session, familia)
    linha = [PontoTemporal(dia=ponto.dia.date(), total=ponto.total) for ponto in serie]

    dias = max(len(linha), 1)
    frequencia = estatisticas.total / dias

    intervalo = None
    if estatisticas.primeiro and estatisticas.ultimo and estatisticas.total > 1:
        janela = (estatisticas.ultimo - estatisticas.primeiro).total_seconds() / 3600
        intervalo = janela / (estatisticas.total - 1)

    return Evidencia(
        vizinhos_da_familia=sum(1 for v in vizinhos if v.fault_family == familia),
        eventos_da_familia=estatisticas.total,
        primeiro_registro=estatisticas.primeiro,
        ultimo_registro=estatisticas.ultimo,
        frequencia_por_dia=round(frequencia, 2),
        intervalo_medio_horas=round(intervalo, 3) if intervalo is not None else None,
        linha_do_tempo=linha,
        contexto_operacional=ContextoOperacional(
            rpm_min=float(estatisticas.rpm_min),
            rpm_max=float(estatisticas.rpm_max),
            rpm_medio=round(float(estatisticas.rpm_medio), 1),
            temp_min=float(estatisticas.temp_min),
            temp_max=float(estatisticas.temp_max),
            temp_media=round(float(estatisticas.temp_media), 2),
        ),
    )


def analisar(
    session: Session,
    vetor: list[float],
    *,
    k: int | None = None,
    confianca_minima: float | None = None,
    excluir_id: int | None = None,
) -> SimilarityResult:
    """Diagnostica um evento pela vizinhanca historica, ou se abstem."""
    settings = get_settings()
    k = k or settings.similarity_k
    limiar = (
        confianca_minima if confianca_minima is not None else settings.similarity_confidence_min
    )

    vizinhos = repo.buscar_vizinhos(session, vetor, k=k, excluir_id=excluir_id)
    if not vizinhos:
        return SimilarityResult(
            familia_diagnosticada=None,
            confianca=0.0,
            motivo="familia_sem_historico",
            e_problema=False,
            vizinhos=[],
            votos=[],
            evidencia=None,
            aviso="Nao ha historico indexado para comparacao.",
        )

    votos, confianca, vencedora = _votar(vizinhos)

    vizinhos_schema = [
        VizinhoSchema(
            id=vizinho.id,
            created_at=vizinho.created_at,
            canonical_fault=vizinho.canonical_fault,
            fault_family=vizinho.fault_family,
            similarity=round(vizinho.similarity, 4),
            rpm=vizinho.rpm,
            temperature_c=vizinho.temperature_c,
        )
        for vizinho in vizinhos
    ]

    evidencia = _montar_evidencia(session, vencedora, vizinhos)

    # Vizinhanca dividida: o sinal nao sustenta um diagnostico.
    if confianca < limiar:
        segunda = votos[1].fault_family if len(votos) > 1 else "-"
        return SimilarityResult(
            familia_diagnosticada=None,
            # A familia mais votada continua sendo informacao util: o tecnico pode
            # confirmar a hipotese em campo. Esconde-la faria a abstencao parecer
            # ausencia de resultado.
            hipotese=vencedora,
            confianca=round(confianca, 4),
            motivo="vizinhanca_dividida",
            e_problema=False,
            vizinhos=vizinhos_schema,
            votos=votos,
            evidencia=evidencia,
            aviso=(
                f"Vizinhanca dividida entre `{vencedora}` ({confianca:.0%}) e "
                f"`{segunda}`. Abaixo do limiar de {limiar:.0%}, o sistema nao "
                "emite diagnostico -- os eventos similares ficam disponiveis para "
                "analise humana."
            ),
        )

    # Estado operacional nao gera prescricao (secao 6 do enunciado).
    if vencedora in STATE_FAMILIES:
        return SimilarityResult(
            familia_diagnosticada=vencedora,
            confianca=round(confianca, 4),
            motivo="estado_operacional",
            e_problema=False,
            vizinhos=vizinhos_schema,
            votos=votos,
            evidencia=evidencia,
            aviso=(
                f"O padrao corresponde ao estado `{vencedora}`, que nao e uma "
                "falha. Nenhuma acao de manutencao e indicada."
            ),
        )

    return SimilarityResult(
        familia_diagnosticada=vencedora,
        confianca=round(confianca, 4),
        motivo="diagnosticado",
        e_problema=True,
        vizinhos=vizinhos_schema,
        votos=votos,
        evidencia=evidencia,
        aviso=None,
    )


def familias_sem_historico(session: Session, todas: set[str]) -> set[str]:
    """Familias que existem na taxonomia mas nao no historico.

    Nunca podem ser diagnosticadas por similaridade. No dataset atual e o caso de
    `falta_fase`: 800 registros, todos no holdout, nenhum no treino.
    """
    return todas - repo.familias_com_historico(session)


def agora() -> datetime:
    return datetime.now()
