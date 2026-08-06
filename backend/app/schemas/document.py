"""Contratos da base documental."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UploadDocResponse(BaseModel):
    document_id: int
    status: str
    arquivo: str
    titulo: str
    familia: str
    familia_descricao: str
    paginas: int
    trechos: int
    metodo: str = Field(description="`text` ou `ocr`")
    confianca_ocr: float | None = None
    ja_existia: bool = Field(
        description="True quando o mesmo arquivo ja estava indexado (dedup por hash)"
    )
    cobertura_atualizada: bool


class DocumentoOut(BaseModel):
    id: int
    arquivo: str
    titulo: str
    familia: str | None
    paginas: int
    trechos: int
    metodo: str
    confianca_ocr: float | None
    status: str
    erro: str | None
    criado_em: datetime


class FamiliaOut(BaseModel):
    familia: str
    descricao: str
    e_problema: bool
    eventos: int
    eventos_holdout: int = Field(
        default=0,
        description=(
            "Leituras disponiveis no conjunto de teste. Familias com zero nao podem "
            "ser demonstradas: existem no historico, mas nao no periodo reservado "
            "para avaliacao."
        ),
    )
    coberta: bool
    documentos: list[str]
