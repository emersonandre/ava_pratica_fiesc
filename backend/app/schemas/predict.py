"""Contrato consolidado de `/api/v1/predict`.

Uma unica resposta traz diagnostico, evidencia estatistica, cobertura documental e
prescricao (ou recusa). Um integrador industrial nao deveria precisar orquestrar
tres chamadas para saber o que fazer com um alarme.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.prescription import Prescricao, Recusa
from app.schemas.sensor_event import SensorEventIn
from app.schemas.similarity import Evidencia, Vizinho, VotoFamilia


class DocumentoConsultado(BaseModel):
    arquivo: str
    titulo: str
    metodo: str = Field(description="`text` ou `ocr`")
    paginas: int


class CoberturaOut(BaseModel):
    familia: str | None
    coberta: bool
    motivo: str
    documentos: list[DocumentoConsultado]


class DiagnosticoOut(BaseModel):
    familia: str | None = Field(description="None quando o sistema se abstem")
    confianca: float
    motivo: str
    e_problema: bool
    votos: list[VotoFamilia]
    aviso: str | None = None


class TemposOut(BaseModel):
    similaridade_ms: float
    cobertura_ms: float
    recuperacao_ms: float
    geracao_ms: float
    verificacao_ms: float
    total_ms: float


class PredictRequest(SensorEventIn):
    pergunta: str | None = Field(
        default=None,
        description="Pergunta do operador. Omitir usa 'Como corrigir esta falha?'.",
    )
    k: int | None = Field(default=None, ge=1, le=200)


class PredictResponse(BaseModel):
    diagnostico: DiagnosticoOut
    evidencia: Evidencia | None
    cobertura: CoberturaOut
    prescricao: Prescricao | None = None
    recusa: Recusa | None = None
    vizinhos: list[Vizinho]
    tempos: TemposOut
    chamou_llm: bool
