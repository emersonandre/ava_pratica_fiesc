"""Log estruturado por requisicao.

Cada requisicao ganha um identificador que aparece no log e no cabecalho de
resposta. Quando alguem reporta "a analise deu errado as 14h32", o identificador
liga a queixa a linha exata do log.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("prescritiva.http")

CABECALHO_ID = "X-Request-ID"

# Rotas de ruido: health e docs sao chamadas o tempo todo por monitoramento e
# pelo navegador, e poluiriam o log sem informar nada.
SILENCIOSAS = frozenset({"/api/health", "/docs", "/redoc", "/openapi.json", "/"})


class LogDeRequisicao(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        identificador = request.headers.get(CABECALHO_ID) or uuid.uuid4().hex[:12]
        inicio = time.perf_counter()

        resposta = await call_next(request)

        duracao_ms = (time.perf_counter() - inicio) * 1000
        resposta.headers[CABECALHO_ID] = identificador

        if request.url.path not in SILENCIOSAS:
            logger.info(
                "req=%s %s %s -> %d em %.0fms",
                identificador,
                request.method,
                request.url.path,
                resposta.status_code,
                duracao_ms,
            )
        return resposta
