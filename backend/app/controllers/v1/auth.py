"""Emissao de token para a superficie externa.

Consumida por sistemas da planta (CMMS, supervisorio, coletor de dados). O
cliente troca credencial por um JWT de vida curta e o envia em
`Authorization: Bearer <token>` nas chamadas a `/api/v1/predict` e
`/api/v1/upload_doc`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import TokenRequest
from app.security import TokenResponse, authenticate_client, create_access_token
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.post("/auth/token", response_model=TokenResponse)
def emitir_token(
    requisicao: TokenRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Troca `client_id` e `client_secret` por um token de acesso.

    A comparacao das credenciais e feita em tempo constante. Credencial invalida
    devolve 401 sem distinguir se o erro foi no identificador ou no segredo --
    diferenciar entregaria ao atacante a informacao de que o `client_id` existe.
    """
    concedidos = authenticate_client(settings, requisicao.client_id, requisicao.client_secret)

    if requisicao.scopes is not None:
        excedentes = set(requisicao.scopes) - set(concedidos)
        if excedentes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Escopos nao concedidos a este cliente: {sorted(excedentes)}.",
            )
        # Principio do menor privilegio: o cliente pode pedir menos do que tem.
        concedidos = requisicao.scopes

    return create_access_token(settings, subject=requisicao.client_id, scopes=concedidos)
