"""Contratos do chat prescritivo.

A observacao 3 do enunciado pede interacao com o modelo durante a apresentacao.
O chat mantem o evento como ancora: perguntas de acompanhamento nao precisam
reenviar a leitura, e continuam sujeitas ao mesmo gate de cobertura.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.predict import TemposOut
from app.schemas.prescription import Citacao, RelatorioEmbasamento
from app.schemas.sensor_event import SensorEventIn

Papel = Literal["operador", "assistente"]


class MensagemChat(BaseModel):
    papel: Papel
    texto: str


class ChatRequest(BaseModel):
    evento: SensorEventIn = Field(description="Leitura que ancora a conversa")
    mensagens: list[MensagemChat] = Field(
        default_factory=list, description="Histórico, do mais antigo ao mais recente"
    )
    pergunta: str
    confianca_minima: float | None = Field(default=None, ge=0, le=1)


class ChatResponse(BaseModel):
    resposta: str
    citacoes: list[Citacao] = Field(default_factory=list)
    embasamento: RelatorioEmbasamento | None = None
    familia: str | None = None
    cobertura: str
    recusou: bool = Field(
        description="True quando o sistema se absteve; nesse caso o modelo nao foi chamado"
    )
    sugestoes: list[str] = Field(
        default_factory=list, description="Perguntas de acompanhamento propostas"
    )
    tempos: TemposOut
