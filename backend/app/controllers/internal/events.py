"""Endpoints internos de evento -- consumidos pelo frontend.

Protegidos por `X-Internal-Key`. A superficie externa (`/api/v1/predict`) usa
JWT e devolve a resposta consolidada com prescricao; aqui o contrato e mais
granular, para a interface montar seus paineis.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.v1 import predict as predict_controller
from app.core.features import load_scaler, to_vector
from app.database import get_session
from app.models import SensorEvent
from app.repositories import sensor_event as repo
from app.schemas.predict import PredictRequest, PredictResponse
from app.schemas.sensor_event import SensorEventIn, SensorEventOut
from app.schemas.similarity import SimilarityResult
from app.security import require_internal_key
from app.services import coverage, similarity
from app.settings import get_settings

router = APIRouter(
    prefix="/api/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


@router.post("/events/similar", response_model=SimilarityResult)
def eventos_similares(
    evento: SensorEventIn,
    session: Annotated[Session, Depends(get_session)],
    k: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> SimilarityResult:
    """Busca por similaridade pura -- sem LLM, sem custo de geracao.

    Separado do `/predict` de proposito: permite demonstrar a camada de dados de
    forma isolada e deixa evidente o que e estatistica e o que e geracao.
    """
    settings = get_settings()
    try:
        scaler = load_scaler(settings.artifacts_path)
    except FileNotFoundError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(erro),
        ) from erro

    vetor = to_vector(scaler, evento.to_feature_dict())
    return similarity.analisar(session, vetor.tolist(), k=k)


def _procurar_por_desfecho(
    session: Session,
    *,
    familia: str | None,
    desfecho: str,
    confianca_minima: float | None,
) -> SensorEvent | None:
    """Percorre candidatos do holdout ate achar um com o desfecho pedido.

    Para `sem_documento` a busca cega raramente encontra: o desfecho exige um
    diagnostico confiante de uma familia que nao tem procedimento, e isso e raro
    no sorteio geral. Quando nenhuma familia foi pedida, a busca passa a
    percorrer justamente as familias descobertas.
    """
    familias = [familia] if familia else [None]

    if desfecho == "sem_documento" and not familia:
        descobertas = coverage.familias_descobertas(session)
        familias = list(descobertas) or [None]

    for alvo in familias:
        for evento in repo.candidatos_holdout(session, familia=alvo):
            resultado = similarity.analisar(
                session,
                [float(v) for v in evento.features],
                confianca_minima=confianca_minima,
            )
            cobertura = coverage.verificar(
                session, resultado.familia_diagnosticada, e_problema=resultado.e_problema
            )
            if cobertura.motivo == _MOTIVO_ESPERADO[desfecho]:
                return evento
    return None


_MOTIVO_ESPERADO = {
    "prescricao": "coberto",
    "sem_documento": "sem_documento",
    "sem_diagnostico": "sem_diagnostico",
}


@router.post("/events/analyze", response_model=PredictResponse)
def analisar(
    requisicao: PredictRequest,
    session: Annotated[Session, Depends(get_session)],
) -> PredictResponse:
    """Mesma analise de `/api/v1/predict`, para o frontend.

    Compartilha a implementacao com a rota externa -- nao ha um segundo caminho
    que possa divergir no comportamento do gate.
    """
    return predict_controller.executar(session, requisicao)


@router.get("/events/sample", response_model=SensorEventOut)
def amostra(
    session: Annotated[Session, Depends(get_session)],
    familia: Annotated[str | None, Query(description="Filtra por familia canonica")] = None,
    desfecho: Annotated[
        Literal["qualquer", "prescricao", "sem_documento", "sem_diagnostico"],
        Query(description="Procura um evento que produza este desfecho"),
    ] = "qualquer",
    confianca_minima: Annotated[float | None, Query(ge=0, le=1)] = None,
) -> SensorEventOut:
    """Um evento real do holdout, para demonstracao com dado nunca visto.

    A amostra vem sempre do holdout (10 a 16/jun). Demonstrar sobre dado de
    treino inflaria o resultado -- o vizinho mais proximo seria o proprio evento.

    O parametro `desfecho` procura um evento que produza determinado resultado.
    Sobre o holdout o sistema se abstem em cerca de dois tercos dos casos; sem
    esse filtro, quem esta assistindo ve varias recusas seguidas e nao consegue
    distinguir "funcionando como projetado" de "quebrado". O evento continua
    sendo real e nunca visto -- muda apenas qual dos casos reais e mostrado.
    """
    if desfecho == "qualquer":
        evento = similarity.repo.amostra_holdout(session, familia=familia)
    else:
        evento = _procurar_por_desfecho(
            session, familia=familia, desfecho=desfecho, confianca_minima=confianca_minima
        )

    if evento is None:
        if desfecho == "qualquer":
            detalhe = f"Nenhum evento de holdout para a familia {familia!r}."
        else:
            limiar = confianca_minima if confianca_minima is not None else "configurado"
            detalhe = (
                f"Nenhuma leitura do conjunto de teste produz o desfecho "
                f"{desfecho!r} com concordancia minima de {limiar}"
                f"{f', na familia {familia!r}' if familia else ''}. "
            )
            if desfecho == "sem_documento":
                detalhe += (
                    "Este desfecho exige diagnosticar com confianca uma familia que "
                    "nao tem procedimento cadastrado -- e as familias descobertas "
                    "(rotor excentrico, ventoinha, falta de fase) raramente sao "
                    "reconhecidas como elas mesmas: os vizinhos se dividem. "
                    "Baixe a concordancia minima para cerca de 50% para encontrar."
                )
            else:
                detalhe += "Ajuste a concordancia minima e tente de novo."
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detalhe)

    return SensorEventOut(
        id=evento.id,
        created_at=evento.created_at,
        z_rms_velocity_mm_s=float(evento.z_rms_velocity_mm_s),
        x_rms_velocity_mm_s=float(evento.x_rms_velocity_mm_s),
        z_peak_acceleration_g=float(evento.z_peak_acceleration_g),
        x_peak_acceleration_g=float(evento.x_peak_acceleration_g),
        z_rms_acceleration_g=float(evento.z_rms_acceleration_g),
        x_rms_acceleration_g=float(evento.x_rms_acceleration_g),
        z_high_freq_rms_accel_g=float(evento.z_high_freq_rms_accel_g),
        x_high_freq_rms_accel_g=float(evento.x_high_freq_rms_accel_g),
        z_kurtosis=float(evento.z_kurtosis),
        x_kurtosis=float(evento.x_kurtosis),
        z_crest_factor=float(evento.z_crest_factor),
        x_crest_factor=float(evento.x_crest_factor),
        z_peak_vel_comp_freq_hz=float(evento.z_peak_vel_comp_freq_hz),
        x_peak_vel_comp_freq_hz=float(evento.x_peak_vel_comp_freq_hz),
        temperature_c=float(evento.temperature_c),
        rpm=float(evento.rpm),
        raw_fault=evento.raw_fault,
        fault_family=evento.fault_family,
        split=evento.split,
    )
