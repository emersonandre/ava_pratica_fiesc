"""Autenticacao da API.

Duas superficies, dois mecanismos -- porque os riscos sao diferentes. Detalhes e
justificativa em `tokens.py` e em `docs/SPEC-FEAT-016/spec.md`.
"""

from app.security.tokens import (
    ALL_SCOPES,
    Scope,
    TokenClaims,
    TokenResponse,
    authenticate_client,
    create_access_token,
    require_internal_key,
    require_scope,
)

__all__ = [
    "ALL_SCOPES",
    "Scope",
    "TokenClaims",
    "TokenResponse",
    "authenticate_client",
    "create_access_token",
    "require_internal_key",
    "require_scope",
]
