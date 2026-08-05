"""Schemas do endpoint de saude."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Estado = Literal["ok", "degradado", "fora"]


class ComponentHealth(BaseModel):
    nome: str
    estado: Estado
    detalhe: str | None = None


class HealthResponse(BaseModel):
    estado: Estado = Field(description="Pior estado entre os componentes")
    componentes: list[ComponentHealth]
