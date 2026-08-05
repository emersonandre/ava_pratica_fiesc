"""Endpoint publico de saude.

Verifica de verdade cada componente. Um `/health` que sempre responde `ok` nao
serve para monitoramento -- so cria a ilusao de que algo esta sendo observado.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select

from app.core.features import scaler_path
from app.database import ping, session_scope
from app.models import Document, SensorEvent
from app.schemas.health import ComponentHealth, HealthResponse
from app.settings import get_settings

router = APIRouter(tags=["health"])

PIOR = {"ok": 0, "degradado": 1, "fora": 2}


@router.get("/api/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    settings = get_settings()
    componentes: list[ComponentHealth] = []

    banco_ok = ping()
    componentes.append(
        ComponentHealth(
            nome="banco",
            estado="ok" if banco_ok else "fora",
            detalhe=None if banco_ok else "sem conexao com o PostgreSQL",
        )
    )

    if banco_ok:
        with session_scope() as session:
            eventos = session.scalar(select(func.count()).select_from(SensorEvent)) or 0
            documentos = session.scalar(select(func.count()).select_from(Document)) or 0
        componentes.append(
            ComponentHealth(
                nome="eventos",
                estado="ok" if eventos else "degradado",
                detalhe=f"{eventos} registros"
                if eventos
                else "base vazia -- rode `python manage.py ingest`",
            )
        )
        componentes.append(
            ComponentHealth(
                nome="documentos",
                estado="ok" if documentos else "degradado",
                detalhe=f"{documentos} indexados" if documentos else "nenhum documento indexado",
            )
        )

    scaler = scaler_path(settings.artifacts_path)
    componentes.append(
        ComponentHealth(
            nome="scaler",
            estado="ok" if scaler.exists() else "fora",
            detalhe=None if scaler.exists() else f"{scaler.name} ausente",
        )
    )

    componentes.append(
        ComponentHealth(
            nome="llm",
            estado="ok" if settings.llm_api_key else "degradado",
            detalhe=f"{settings.llm_provider}/{settings.llm_model}"
            if settings.llm_api_key
            else "LLM_API_KEY nao configurada",
        )
    )

    geral = max(componentes, key=lambda componente: PIOR[componente.estado]).estado
    if geral == "fora":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(estado=geral, componentes=componentes)
