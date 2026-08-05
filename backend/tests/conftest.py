"""Fixtures compartilhadas."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.database import ping, session_scope
from app.models import SensorEvent

precisa_banco = pytest.mark.skipif(
    not ping(), reason="banco indisponivel -- suba com `docker compose up -d db`"
)


@pytest.fixture(scope="session")
def session():
    with session_scope() as sessao:
        yield sessao


@pytest.fixture(scope="session")
def base_populada(session) -> bool:
    total = session.scalar(select(func.count()).select_from(SensorEvent)) or 0
    if not total:
        pytest.skip("base vazia -- rode `python manage.py ingest`")
    return True
