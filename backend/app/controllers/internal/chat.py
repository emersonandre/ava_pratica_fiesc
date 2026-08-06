"""Chat prescritivo -- consumido pelo frontend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.features import MissingFeatureError
from app.database import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.predict import TemposOut
from app.security import require_internal_key
from app.services import chat as servico
from app.services import pipeline

router = APIRouter(
    prefix="/api/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


@router.post("/chat", response_model=ChatResponse)
def conversar(
    requisicao: ChatRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ChatResponse:
    """Pergunta ancorada em uma leitura de sensor.

    Passa pelas mesmas camadas da prescricao: gate de cobertura antes do modelo,
    recuperacao filtrada por familia, citacao obrigatoria e verificacao de
    embasamento. O historico entra no prompt, mas cada pergunta recupera trechos
    de novo -- responder de memoria e onde o modelo inventa.
    """
    if not requisicao.pergunta.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A pergunta esta vazia.",
        )

    if not pipeline.pergunta_no_dominio(requisicao.pergunta):
        return ChatResponse(
            resposta=(
                "Esta pergunta nao trata de manutencao industrial. Respondo apenas "
                "sobre falhas, diagnostico e correcao de maquinas rotativas, e "
                "sempre com base na documentacao tecnica cadastrada."
            ),
            cobertura="fora_de_dominio",
            recusou=True,
            tempos=TemposOut(
                similaridade_ms=0,
                cobertura_ms=0,
                recuperacao_ms=0,
                geracao_ms=0,
                verificacao_ms=0,
                total_ms=0,
            ),
        )

    try:
        return servico.conversar(session, requisicao)
    except MissingFeatureError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)
        ) from erro
    except FileNotFoundError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(erro)
        ) from erro
