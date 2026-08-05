"""Autenticacao da API.

Duas superficies, dois mecanismos -- porque os riscos sao diferentes:

**Externa** (`/api/v1/predict`, `/api/v1/upload_doc`): consumida por sistemas da
planta (CMMS, supervisorio, coletor de dados). Usa JWT `Bearer` no cabecalho
`Authorization`. Token com expiracao curta, emitido em `/api/v1/auth/token` contra
credencial de cliente. Cada token carrega escopo, entao um integrador que so le
nao consegue injetar documento na base de conhecimento.

**Interna** (`/api/internal/*`): consumida apenas pelo frontend, dentro da rede.
Usa chave estatica no cabecalho `X-Internal-Key`, definida no `.env`. A chave fica
no proxy do container do frontend e nunca e enviada ao navegador -- por isso nao
faz sentido exigir o ciclo de emissao/renovacao de JWT aqui.
"""

from __future__ import annotations

import hmac
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.settings import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)

Scope = Literal["predict", "upload"]
ALL_SCOPES: tuple[Scope, ...] = ("predict", "upload")


class TokenClaims(BaseModel):
    sub: str
    scopes: list[str]
    exp: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scopes: list[str]


def create_access_token(settings: Settings, subject: str, scopes: list[str]) -> TokenResponse:
    expires_in = settings.jwt_expire_minutes * 60
    payload = {
        "sub": subject,
        "scopes": scopes,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
        "iss": "manutencao-prescritiva",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return TokenResponse(access_token=token, expires_in=expires_in, scopes=scopes)


def authenticate_client(settings: Settings, client_id: str, client_secret: str) -> list[str]:
    """Valida credencial de cliente em tempo constante."""
    id_ok = hmac.compare_digest(client_id, settings.api_client_id)
    secret_ok = hmac.compare_digest(client_secret, settings.api_client_secret)
    if not (id_ok and secret_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial de cliente invalida.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return list(ALL_SCOPES)


def _decode(settings: Settings, token: str) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer="manutencao-prescritiva",
        )
    except jwt.ExpiredSignatureError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Solicite um novo em /api/v1/auth/token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro
    except jwt.InvalidTokenError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro
    return TokenClaims(**payload)


def require_scope(scope: Scope):
    """Dependencia dos endpoints externos: exige JWT valido com o escopo pedido."""

    def dependency(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> TokenClaims:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cabecalho Authorization: Bearer <token> ausente.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        claims = _decode(settings, credentials.credentials)
        if scope not in claims.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token sem o escopo necessario: {scope}.",
            )
        return claims

    return dependency


def require_internal_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_internal_key: Annotated[str | None, Header(alias="X-Internal-Key")] = None,
) -> None:
    """Dependencia dos endpoints internos: chave compartilhada com o frontend."""
    if not settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_API_KEY nao configurada no servidor.",
        )
    if x_internal_key is None or not hmac.compare_digest(x_internal_key, settings.internal_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabecalho X-Internal-Key ausente ou invalido.",
        )
