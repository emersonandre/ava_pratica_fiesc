"""Endpoints internos de evento -- consumidos pelo frontend.

Protegidos por `X-Internal-Key`. A superficie externa (`/api/v1/predict`) usa
JWT e devolve a resposta consolidada com prescricao; aqui o contrato e mais
granular, para a interface montar seus paineis.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.features import load_scaler, to_vector
from app.database import get_session
from app.schemas.sensor_event import SensorEventIn, SensorEventOut
from app.schemas.similarity import SimilarityResult
from app.security import require_internal_key
from app.services import similarity
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


@router.get("/events/sample", response_model=SensorEventOut)
def amostra(
    session: Annotated[Session, Depends(get_session)],
    familia: Annotated[str | None, Query(description="Filtra por familia canonica")] = None,
) -> SensorEventOut:
    """Um evento real do holdout, para demonstracao com dado nunca visto.

    A amostra vem sempre do holdout (10 a 16/jun). Demonstrar sobre dado de
    treino inflaria o resultado -- o vizinho mais proximo seria o proprio evento.
    """
    evento = similarity.repo.amostra_holdout(session, familia=familia)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum evento de holdout para a familia {familia!r}.",
        )

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
