"""Base declarativa do SQLAlchemy.

Fica isolada em seu proprio modulo para quebrar o ciclo de importacao: os modulos
de `app/models/` importam `Base` daqui, e `app/models/__init__.py` importa todos
eles para registrar as tabelas no metadata.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
