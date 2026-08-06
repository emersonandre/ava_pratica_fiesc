"""POST /api/v1/events -- entrada de leituras do chao de fabrica.

Fecha o ciclo do enunciado: os sensores enviam leituras continuamente para a
base, o sistema analisa contra o historico e devolve o que fazer.

Sem este endpoint a base so poderia ser alimentada pela carga em lote do CSV --
o `/predict` consulta, nao grava.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.v1.predict import montar_resposta
from app.core.features import MissingFeatureError
from app.database import get_session
from app.schemas.ingest import IngestRequest, IngestResponse
from app.schemas.predict import PredictResponse
from app.security import require_scope
from app.services import ingestion, pipeline

logger = logging.getLogger("prescritiva.api")

router = APIRouter(prefix="/api/v1", tags=["v1"])


class IngestComAnalise(IngestResponse):
    analise: PredictResponse | None = None


@router.post(
    "/events",
    response_model=IngestComAnalise,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("ingest"))],
    summary="Recebe leituras de sensor e grava na base de analise",
)
def receber_leituras(
    requisicao: IngestRequest,
    session: Annotated[Session, Depends(get_session)],
) -> IngestComAnalise:
    """Grava uma leitura ou um lote no banco de analise.

    Aceita exatamente o JSON de exemplo da secao 2 do enunciado, incluindo o
    campo `fault` com a condicao anotada pelo operador.

    Comportamento com dado incompleto -- ambos gravam em vez de recusar, porque a
    medicao do sensor vale mais que o rotulo:

    - **sem `fault`**: grava como leitura nao anotada. Entra no historico para
      registro, mas nao participa da votacao de similaridade.
    - **`fault` fora da taxonomia**: idem, e o rotulo volta em
      `rotulos_desconhecidos` para alguem decidir se vira uma familia nova.

    Com `analisar: true`, devolve tambem o diagnostico da ultima leitura do lote
    -- util para o coletor decidir se abre um chamado na hora.
    """
    try:
        resposta = ingestion.ingerir(session, requisicao.leituras)
    except MissingFeatureError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)
        ) from erro
    except FileNotFoundError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{erro} A base precisa estar carregada antes de receber leituras.",
        ) from erro

    analise = None
    if requisicao.analisar:
        ultima = requisicao.leituras[-1]
        # A leitura acabou de entrar como `producao`, e o indice de similaridade
        # cobre esse split -- entao ela apareceria como vizinha de si mesma, com
        # similaridade 1,0, dominando a votacao. `excluir_id` a tira da busca.
        gravada = resposta.leituras[-1]
        resultado = pipeline.analisar_evento(
            session,
            ultima.metricas(),
            gerar_prescricao=False,
            excluir_id=gravada.id,
        )
        analise = montar_resposta(resultado)

    return IngestComAnalise(**resposta.model_dump(), analise=analise)
