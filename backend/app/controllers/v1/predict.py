"""POST /api/v1/predict -- superficie externa.

Consumida por sistemas da planta. Recebe o JSON de metricas do sensor, roda o
motor de similaridade, busca os documentos no banco vetorial, chama o LLM e
devolve um JSON consolidado.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.features import MissingFeatureError
from app.database import get_session
from app.schemas.predict import (
    CoberturaOut,
    DiagnosticoOut,
    DocumentoConsultado,
    PredictRequest,
    PredictResponse,
    TemposOut,
)
from app.schemas.prescription import Prescricao
from app.security import require_scope
from app.services import pipeline
from app.services.pipeline import ResultadoAnalise

logger = logging.getLogger("prescritiva.api")

router = APIRouter(prefix="/api/v1", tags=["v1"])


def montar_resposta(resultado: ResultadoAnalise) -> PredictResponse:
    """Traducao do resultado do pipeline para o contrato publico."""
    similaridade = resultado.similaridade
    cobertura = resultado.cobertura
    prescricao = resultado.resposta if isinstance(resultado.resposta, Prescricao) else None

    return PredictResponse(
        diagnostico=DiagnosticoOut(
            familia=similaridade.familia_diagnosticada,
            confianca=similaridade.confianca,
            motivo=similaridade.motivo,
            e_problema=similaridade.e_problema,
            votos=similaridade.votos,
            aviso=similaridade.aviso,
        ),
        evidencia=similaridade.evidencia,
        cobertura=CoberturaOut(
            familia=cobertura.familia,
            coberta=cobertura.coberta,
            motivo=cobertura.motivo,
            documentos=[
                DocumentoConsultado(
                    arquivo=documento.arquivo,
                    titulo=documento.titulo,
                    metodo=documento.metodo,
                    paginas=documento.paginas,
                )
                for documento in cobertura.documentos
            ],
        ),
        prescricao=prescricao,
        recusa=None if prescricao else resultado.resposta,
        vizinhos=similaridade.vizinhos,
        tempos=TemposOut(
            similaridade_ms=resultado.tempos.similaridade_ms,
            cobertura_ms=resultado.tempos.cobertura_ms,
            recuperacao_ms=resultado.tempos.recuperacao_ms,
            geracao_ms=resultado.tempos.geracao_ms,
            verificacao_ms=resultado.tempos.verificacao_ms,
            total_ms=resultado.tempos.total_ms,
        ),
        chamou_llm=resultado.chamou_llm,
    )


def executar(session: Session, requisicao: PredictRequest) -> PredictResponse:
    """Fluxo compartilhado entre a rota externa e a interna."""
    pergunta = requisicao.pergunta or pipeline.PERGUNTA_PADRAO

    # Pergunta fora do dominio e recusada antes de qualquer processamento.
    if requisicao.pergunta and not pipeline.pergunta_no_dominio(pergunta):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A pergunta nao trata de manutencao industrial. Este sistema responde "
                "apenas sobre falhas, diagnostico e correcao de maquinas rotativas."
            ),
        )

    try:
        resultado = pipeline.analisar_evento(
            session,
            requisicao.to_feature_dict(),
            pergunta=pergunta,
            k=requisicao.k,
            confianca_minima=requisicao.confianca_minima
        )
    except MissingFeatureError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)
        ) from erro
    except FileNotFoundError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(erro)
        ) from erro

    return montar_resposta(resultado)


@router.post(
    "/predict",
    response_model=PredictResponse,
    dependencies=[Depends(require_scope("predict"))],
    summary="Analisa um evento de sensor e devolve diagnostico e prescricao",
)
def predict(
    requisicao: PredictRequest,
    session: Annotated[Session, Depends(get_session)],
) -> PredictResponse:
    """Aceita exatamente o JSON de exemplo da secao 2 do enunciado.

    Campos extras do payload original (`id`, `created_at`, `fault`, colunas em
    unidade imperial) sao aceitos e ignorados -- o integrador nao precisa filtrar
    nada antes de enviar.

    Quando nao ha documentacao para a falha identificada, a resposta traz `recusa`
    em vez de `prescricao`, e **o modelo de linguagem nao e chamado**.
    """
    return executar(session, requisicao)
