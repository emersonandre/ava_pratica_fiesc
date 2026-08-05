"""Contratos da busca por similaridade."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

MotivoAbstencao = Literal[
    "diagnosticado",
    "vizinhanca_dividida",
    "familia_sem_historico",
    "estado_operacional",
]


class Vizinho(BaseModel):
    id: int
    created_at: datetime
    canonical_fault: str
    fault_family: str
    similarity: float = Field(description="Similaridade cosseno em [0, 1]")
    rpm: float
    temperature_c: float


class VotoFamilia(BaseModel):
    fault_family: str
    vizinhos: int = Field(description="Quantos dos k vizinhos pertencem a familia")
    peso: float = Field(description="Fracao do voto ponderado por similaridade")


class PontoTemporal(BaseModel):
    dia: date
    total: int


class ContextoOperacional(BaseModel):
    rpm_min: float
    rpm_max: float
    rpm_medio: float
    temp_min: float
    temp_max: float
    temp_media: float


class Evidencia(BaseModel):
    """Numeros vindos do banco. Nenhum valor aqui passa por LLM."""

    vizinhos_da_familia: int = Field(
        description="Quantos dos k vizinhos recuperados pertencem a familia diagnosticada"
    )
    eventos_da_familia: int = Field(description="Total de eventos da familia em todo o historico")
    primeiro_registro: datetime | None
    ultimo_registro: datetime | None
    frequencia_por_dia: float
    intervalo_medio_horas: float | None
    linha_do_tempo: list[PontoTemporal]
    contexto_operacional: ContextoOperacional | None


class SimilarityResult(BaseModel):
    familia_diagnosticada: str | None = Field(description="None quando o sistema se abstem")
    confianca: float = Field(description="Concentracao do voto ponderado, em [0, 1]")
    motivo: MotivoAbstencao
    e_problema: bool = Field(
        description="False para estados operacionais (normal, motor_desligado...)"
    )
    vizinhos: list[Vizinho]
    votos: list[VotoFamilia]
    evidencia: Evidencia | None
    aviso: str | None = Field(default=None, description="Explicacao quando o sistema se abstem")
