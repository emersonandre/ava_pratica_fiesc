"""Cria extensao, tabelas e indices. Idempotente.

python manage.py initdb
python manage.py initdb --drop     # recria do zero
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.features import FEATURE_DIM
from app.database import get_engine
from app.models import Base
from app.settings import get_settings


def run(*, drop: bool = False) -> int:
    settings = get_settings()
    engine = get_engine()

    with engine.begin() as connection:
        # pgvector precisa existir antes de qualquer coluna Vector ser criada.
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        versao = connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one()
        print(f"pgvector       {versao}")

    if drop:
        Base.metadata.drop_all(engine)
        print("tabelas        removidas")

    Base.metadata.create_all(engine)

    with engine.connect() as connection:
        tabelas = (
            connection.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
            .scalars()
            .all()
        )

    print(f"vetor sensor   {FEATURE_DIM} dimensoes")
    print(f"vetor doc      {settings.embedding_dim} dimensoes ({settings.embedding_model})")
    print(f"tabelas        {', '.join(tabelas)}")
    return 0
