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
    rotulo_real: str | None = Field(
        default=None,
        description="Familia canonica do `fault` informado, quando houver. Gabarito.",
    )
    acertou: bool | None = Field(
        default=None,
        description="Comparacao entre o diagnostico e o gabarito. None sem gabarito.",
    )
    hipotese: str | None = Field(
        default=None,
        description="Familia mais votada quando ha abstencao. Nao libera prescricao.",
    )
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
    fault: str | None = Field(
        default=None,
        description=(
            "Condicao anotada pelo operador, quando conhecida. Nao influencia o "
            "diagnostico -- serve de gabarito: a resposta devolve a familia canonica "
            "correspondente em `rotulo_real`, para comparar com o que o sistema "
            "concluiu. A normalizacao acontece aqui porque a taxonomia vive no "
            "backend; o cliente nao tem como saber que `cocked_rotor_2` e `cocked_rotor`."
        ),
    )
    pergunta: str | None = Field(
        default=None,
        description="Pergunta do operador. Omitir usa 'Como corrigir esta falha?'.",
    )
    k: int | None = Field(default=None, ge=1, le=200)
    gerar_prescricao: bool = Field(
        default=True,
        description=(
            "Quando falso, a analise para depois do gate de cobertura e nao chama "
            "o modelo. Serve para separar as duas etapas na interface: identificar "
            "a falha responde em milissegundos, redigir o procedimento leva dezenas "
            "de segundos."
        ),
    )
    confianca_minima: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description=(
            "Concordancia minima da vizinhanca para o sistema emitir diagnostico. "
            "Omitir usa o valor de SIMILARITY_CONFIDENCE_MIN. Expor este parametro "
            "torna a troca entre cobertura e precisao inspecionavel: baixar o limiar "
            "aumenta a fracao de eventos diagnosticados e reduz o acerto."
        ),
    )


class PredictResponse(BaseModel):
    diagnostico: DiagnosticoOut
    evidencia: Evidencia | None
    cobertura: CoberturaOut
    prescricao: Prescricao | None = None
    recusa: Recusa | None = None
    vizinhos: list[Vizinho]
    tempos: TemposOut
    chamou_llm: bool
