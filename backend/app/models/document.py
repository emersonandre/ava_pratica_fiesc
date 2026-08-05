"""Documento tecnico da empresa (manual, procedimento, relatorio)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))

    # Familia de falha que o documento cobre. Informada por quem registra o
    # documento -- nao inferida pelo modelo, para nao introduzir erro justamente
    # no mecanismo que sustenta a regra antialucinacao.
    fault_family: Mapped[str | None] = mapped_column(String(40), index=True)

    pages: Mapped[int] = mapped_column(Integer)
    # `text` = PDF com camada de texto; `ocr` = paginas em imagem, transcritas.
    extraction_method: Mapped[str] = mapped_column(String(10))
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    # Deduplicacao: reenviar o mesmo arquivo nao reindexa nem duplica chunks.
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','processing','indexed','failed')",
            name="ck_documents_status",
        ),
        CheckConstraint(
            "extraction_method IN ('text','ocr')", name="ck_documents_extraction_method"
        ),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} {self.filename!r} status={self.status}>"
