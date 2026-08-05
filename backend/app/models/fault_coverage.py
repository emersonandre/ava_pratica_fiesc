"""Mapa familia de falha -> documento que a cobre.

Tabela que sustenta o gate deterministico da SPEC-FEAT-008: sem linha aqui para a
familia diagnosticada, o LLM nao e chamado e o sistema responde que ainda nao
existe documentacao para o problema identificado.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FaultCoverage(Base):
    __tablename__ = "fault_document_coverage"

    id: Mapped[int] = mapped_column(primary_key=True)
    fault_family: Mapped[str] = mapped_column(String(40), index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    # Como o vinculo foi estabelecido: `manual` (revisado) ou `upload` (registro novo).
    source: Mapped[str] = mapped_column(String(20), default="manual")
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("fault_family", "document_id", name="uq_coverage_family_document"),
    )

    def __repr__(self) -> str:
        return f"<FaultCoverage {self.fault_family} -> doc {self.document_id}>"
