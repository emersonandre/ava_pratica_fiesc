"""Estatisticas, cobertura e documentos -- consumidos pelo dashboard."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.controllers.v1.upload_doc import upload_doc
from app.core.features import METRIC_COLUMNS
from app.core.taxonomy import (
    FAMILY_DESCRIPTIONS,
    PROBLEM_FAMILIES,
)
from app.database import get_session
from app.repositories import document as repo
from app.schemas.document import DocumentoOut, FamiliaOut, UploadDocResponse
from app.security import require_internal_key
from app.services import coverage

router = APIRouter(
    prefix="/api/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


class VisaoGeral(BaseModel):
    total_eventos: int
    eventos_problema: int
    familias: int
    familias_problema: int
    familias_cobertas: int
    familias_descobertas: list[str]
    documentos_indexados: int
    trechos_indexados: int
    periodo_inicio: date | None
    periodo_fim: date | None
    eventos_holdout: int
    ranking: list[FamiliaOut]


class PontoLinhaDoTempo(BaseModel):
    dia: date
    familia: str
    total: int


class FaixaDaFamilia(BaseModel):
    familia: str
    leituras: int
    p10: float
    p25: float
    mediana: float
    p75: float
    p90: float


class Distribuicao(BaseModel):
    metrica: str
    unidade: str
    familias: list[FaixaDaFamilia]


class FrequenciaDaFamilia(BaseModel):
    familia: str
    e_problema: bool
    leituras: int
    primeira: date
    ultima: date
    dias_com_ocorrencia: int
    leituras_por_dia: float
    intervalo_medio_dias: float | None


# A unidade nao sai do nome da coluna: `_g` e aceleracao em gravidade, mas `_hz`
# e frequencia -- um sufixo so nao basta para rotular o eixo.
UNIDADES: dict[str, str] = {
    "z_rms_velocity_mm_s": "mm/s",
    "x_rms_velocity_mm_s": "mm/s",
    "z_peak_velocity_mm_s": "mm/s",
    "x_peak_velocity_mm_s": "mm/s",
    "z_peak_acceleration_g": "g",
    "x_peak_acceleration_g": "g",
    "z_rms_acceleration_g": "g",
    "x_rms_acceleration_g": "g",
    "z_high_freq_rms_accel_g": "g",
    "x_high_freq_rms_accel_g": "g",
    "z_kurtosis": "",
    "x_kurtosis": "",
    "z_crest_factor": "",
    "x_crest_factor": "",
    "z_peak_vel_comp_freq_hz": "Hz",
    "x_peak_vel_comp_freq_hz": "Hz",
    "temperature_c": "°C",
    "rpm": "RPM",
}


@router.get("/stats/overview", response_model=VisaoGeral)
def visao_geral(session: Annotated[Session, Depends(get_session)]) -> VisaoGeral:
    """KPIs do dashboard, em uma chamada so.

    A cobertura documental entra como indicador de primeira linha: e o diferencial
    conceitual da solucao -- o sistema sabe o que nao sabe.
    """
    geral = repo.visao_geral(session)
    contagens = repo.contagem_por_familia(session)
    no_holdout = repo.contagem_holdout_por_familia(session)
    mapa = coverage.mapa_de_cobertura(session)
    documentos = repo.listar_documentos(session)

    ranking = sorted(
        (
            FamiliaOut(
                familia=familia,
                descricao=FAMILY_DESCRIPTIONS.get(familia, ""),
                e_problema=familia in PROBLEM_FAMILIES,
                eventos=contagens.get(familia, 0),
                eventos_holdout=no_holdout.get(familia, 0),
                coberta=bool(mapa.get(familia)),
                documentos=[d.arquivo for d in mapa.get(familia, ())],
            )
            for familia in contagens
        ),
        key=lambda item: item.eventos,
        reverse=True,
    )

    descobertas = [f for f, docs in mapa.items() if not docs]

    return VisaoGeral(
        total_eventos=geral.total_eventos,
        eventos_problema=geral.eventos_problema,
        familias=geral.familias,
        familias_problema=len(PROBLEM_FAMILIES),
        familias_cobertas=len(PROBLEM_FAMILIES) - len(descobertas),
        familias_descobertas=sorted(descobertas),
        documentos_indexados=sum(1 for d, _ in documentos if d.status == "indexed"),
        trechos_indexados=sum(trechos for _, trechos in documentos),
        periodo_inicio=geral.periodo_inicio.date() if geral.periodo_inicio else None,
        periodo_fim=geral.periodo_fim.date() if geral.periodo_fim else None,
        eventos_holdout=geral.holdout,
        ranking=ranking,
    )


@router.get("/stats/timeline", response_model=list[PontoLinhaDoTempo])
def linha_do_tempo(
    session: Annotated[Session, Depends(get_session)],
    familia: Annotated[str | None, Query()] = None,
    desde: Annotated[date | None, Query()] = None,
) -> list[PontoLinhaDoTempo]:
    """Distribuicao temporal das ocorrencias, item pedido na secao 3 do enunciado."""
    return [
        PontoLinhaDoTempo(dia=linha.dia.date(), familia=linha.fault_family, total=linha.total)
        for linha in repo.linha_do_tempo(session, familia=familia, inicio=desde)
    ]


@router.get("/stats/distribution", response_model=Distribuicao)
def distribuicao(
    session: Annotated[Session, Depends(get_session)],
    metrica: Annotated[str, Query(description="Coluna de METRIC_COLUMNS")] = (
        "z_rms_velocity_mm_s"
    ),
) -> Distribuicao:
    """Faixa de valores de uma metrica em cada familia.

    O nome da coluna e conferido contra a lista fechada antes de chegar na
    consulta: o repositorio resolve o atributo dinamicamente, e aceitar texto
    livre aqui abriria a porta para consultar qualquer coluna do modelo.
    """
    if metrica not in METRIC_COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Metrica desconhecida. Disponiveis: {', '.join(METRIC_COLUMNS)}",
        )

    return Distribuicao(
        metrica=metrica,
        unidade=UNIDADES.get(metrica, ""),
        familias=[
            FaixaDaFamilia(
                familia=linha.fault_family,
                leituras=linha.leituras,
                p10=float(linha.p10),
                p25=float(linha.p25),
                mediana=float(linha.mediana),
                p75=float(linha.p75),
                p90=float(linha.p90),
            )
            for linha in repo.distribuicao_por_familia(session, metrica=metrica)
        ],
    )


@router.get("/stats/frequency", response_model=list[FrequenciaDaFamilia])
def frequencia(
    session: Annotated[Session, Depends(get_session)],
) -> list[FrequenciaDaFamilia]:
    """Com que frequencia cada falha aparece e o intervalo medio entre ocorrencias.

    A secao 1 do enunciado pede as duas coisas na saida do sistema. Aqui elas
    aparecem no agregado, para a equipe ver quais falhas sao recorrentes; a
    resposta de um evento especifico traz os mesmos numeros so daquela familia.

    Contado em dias, e nao em leituras: numa bancada de ensaio o coletor amostra
    a cada poucos segundos, e o intervalo entre leituras mede a cadencia do
    equipamento -- nao com que frequencia o defeito acontece.
    """
    saida: list[FrequenciaDaFamilia] = []
    for linha in repo.frequencia_por_familia(session):
        dias_de_periodo = (linha.ultima.date() - linha.primeira.date()).days
        saida.append(
            FrequenciaDaFamilia(
                familia=linha.fault_family,
                e_problema=linha.fault_family in PROBLEM_FAMILIES,
                leituras=linha.leituras,
                primeira=linha.primeira.date(),
                ultima=linha.ultima.date(),
                dias_com_ocorrencia=linha.dias_com_ocorrencia,
                leituras_por_dia=linha.leituras / max(linha.dias_com_ocorrencia, 1),
                # Um unico dia nao define intervalo. Devolver zero seria pior que
                # devolver nada: leria como "acontece o tempo todo".
                intervalo_medio_dias=(
                    dias_de_periodo / (linha.dias_com_ocorrencia - 1)
                    if linha.dias_com_ocorrencia > 1 and dias_de_periodo > 0
                    else None
                ),
            )
        )
    return saida


@router.get("/faults", response_model=list[FamiliaOut])
def familias(session: Annotated[Session, Depends(get_session)]) -> list[FamiliaOut]:
    """Familias canonicas com status de cobertura documental."""
    contagens = repo.contagem_por_familia(session)
    no_holdout = repo.contagem_holdout_por_familia(session)
    mapa = coverage.mapa_de_cobertura(session)

    return [
        FamiliaOut(
            familia=familia,
            descricao=FAMILY_DESCRIPTIONS.get(familia, ""),
            e_problema=familia in PROBLEM_FAMILIES,
            eventos=contagens.get(familia, 0),
            eventos_holdout=no_holdout.get(familia, 0),
            coberta=bool(mapa.get(familia)),
            documentos=[d.arquivo for d in mapa.get(familia, ())],
        )
        for familia in sorted(FAMILY_DESCRIPTIONS)
    ]


@router.post(
    "/documents",
    response_model=UploadDocResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_documento(
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File()],
    fault_family: Annotated[str, Form()],
    title: Annotated[str | None, Form()] = None,
) -> UploadDocResponse:
    """Upload pelo frontend.

    Mesma implementacao de `/api/v1/upload_doc`, com a autenticacao da superficie
    interna. O frontend usa chave estatica, nao JWT -- e nao teria como obter um
    token sem embutir a credencial de cliente no bundle.
    """
    return await upload_doc(session=session, file=file, fault_family=fault_family, title=title)


@router.get("/documents", response_model=list[DocumentoOut])
def documentos(session: Annotated[Session, Depends(get_session)]) -> list[DocumentoOut]:
    """Documentos indexados e estado da indexacao."""
    return [
        DocumentoOut(
            id=documento.id,
            arquivo=documento.filename,
            titulo=documento.title,
            familia=documento.fault_family,
            paginas=documento.pages,
            trechos=trechos,
            metodo=documento.extraction_method,
            confianca_ocr=(
                float(documento.ocr_confidence) if documento.ocr_confidence else None
            ),
            status=documento.status,
            erro=documento.error,
            criado_em=documento.created_at,
        )
        for documento, trechos in repo.listar_documentos(session)
    ]
