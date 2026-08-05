"""Contratos de autenticacao da superficie externa."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.security import ALL_SCOPES


class TokenRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": "cliente-planta-a1b2c3d4",
                "client_secret": "...",
                "scopes": list(ALL_SCOPES),
            }
        }
    )

    client_id: str
    client_secret: str
    scopes: list[str] | None = Field(
        default=None,
        description=(
            "Escopos desejados. Omitir concede todos os do cliente. "
            "Pedir um subconjunto e a forma de emitir um token de menor privilegio "
            "-- por exemplo, um coletor de dados que so consulta."
        ),
    )
