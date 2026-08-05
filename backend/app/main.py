"""Fabrica da aplicacao ASGI.

Camadas (padrao MVC adaptado a uma API):

    controllers/   rotas HTTP -- traduzem requisicao em chamada de servico   (Controller)
    services/      regra de negocio: similaridade, RAG, cobertura, prescricao
    repositories/  acesso a dados -- todas as consultas ficam aqui
    models/        entidades e schema do banco                                (Model)
    schemas/       contratos de entrada e saida da API                        (View)
    core/          dominio puro: taxonomia e features (sem IO)
    integrations/  fronteiras externas: LLM, embeddings, OCR

A regra que mantem isso honesto: um controller nunca monta consulta SQL, e um
repositorio nunca chama LLM.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.controllers import health
from app.controllers.internal import events as internal_events
from app.settings import get_settings

logger = logging.getLogger("prescritiva")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    # Uma API industrial no ar sem autenticacao e pior que uma API fora do ar:
    # o problema so aparece depois. Melhor nao subir.
    settings.require_auth()
    logger.info(
        "api iniciada provider=%s modelo=%s embeddings=%s",
        settings.llm_provider,
        settings.llm_model,
        settings.embedding_model,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Manutencao Prescritiva",
        description=(
            "Busca por similaridade em historico de sensores + RAG sobre a base "
            "documental da empresa. Duas superficies: `/api/v1` (externa, JWT) e "
            "`/api/internal` (frontend, chave estatica)."
        ),
        version="0.1.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "health", "description": "Estado do sistema"},
            {"name": "v1", "description": "Superficie externa -- exige JWT Bearer"},
            {"name": "internal", "description": "Superficie interna -- exige X-Internal-Key"},
        ],
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(internal_events.router)

    @application.get("/", include_in_schema=False)
    def raiz() -> RedirectResponse:
        """A raiz nao serve conteudo -- manda para a documentacao interativa.

        Sem isso, abrir a URL do servico no navegador devolve 404 e parece que a
        API nao subiu.
        """
        return RedirectResponse(url="/docs")

    return application


app = create_app()
