"""Metadado do indice vetorial.

Trocar o modelo de embedding sem reindexar corromperia o indice em silencio: os
vetores antigos e os novos viveriam no mesmo espaco sem serem comparaveis. Com o
modelo e a dimensao gravados, a divergencia e detectada e bloqueada com erro claro.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IndexMetadata(Base):
    __tablename__ = "index_metadata"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<IndexMetadata {self.key}={self.value!r}>"
