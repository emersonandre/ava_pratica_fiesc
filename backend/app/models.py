"""Schema do banco.

Um unico PostgreSQL guarda tudo: os eventos de sensor com seu vetor de features e
os documentos com seus embeddings. Com `pgvector` nos dois casos, a busca por
similaridade de sinal e a busca semantica em documento usam o mesmo mecanismo, e
da para cruzar vizinhanca de sensor com metadado de falha em uma consulta SQL so.
"""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import get_settings
from app.core.features import FEATURE_DIM

EMBEDDING_DIM = get_settings().embedding_dim


class Base(DeclarativeBase):
    pass


class SensorEvent(Base):
    """Um registro de sensor do banner.csv, ja normalizado e vetorizado."""

    __tablename__ = "sensor_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # Rotulo bruto preservado para auditoria; canonico e familia vem da SPEC-FEAT-002.
    raw_fault: Mapped[str] = mapped_column(String(80))
    canonical_fault: Mapped[str] = mapped_column(String(80), index=True)
    fault_family: Mapped[str] = mapped_column(String(40), index=True)
    is_problem: Mapped[bool] = mapped_column(Boolean)

    # `train` = ate 09/jun; `holdout` = rotulos new_*, de 10 a 16/jun.
    # Corte temporal natural do dataset, sem sorteio -- evita que amostras da mesma
    # sessao de ensaio (coletadas com segundos de diferenca) caiam dos dois lados.
    split: Mapped[str] = mapped_column(String(10), index=True)

    # Colunas metricas originais, preservadas para exibicao e analise.
    z_rms_velocity_mm_s: Mapped[float] = mapped_column(Numeric(12, 4))
    x_rms_velocity_mm_s: Mapped[float] = mapped_column(Numeric(12, 4))
    z_peak_velocity_mm_s: Mapped[float] = mapped_column(Numeric(12, 4))
    x_peak_velocity_mm_s: Mapped[float] = mapped_column(Numeric(12, 4))
    z_peak_acceleration_g: Mapped[float] = mapped_column(Numeric(12, 4))
    x_peak_acceleration_g: Mapped[float] = mapped_column(Numeric(12, 4))
    z_rms_acceleration_g: Mapped[float] = mapped_column(Numeric(12, 4))
    x_rms_acceleration_g: Mapped[float] = mapped_column(Numeric(12, 4))
    z_high_freq_rms_accel_g: Mapped[float] = mapped_column(Numeric(12, 4))
    x_high_freq_rms_accel_g: Mapped[float] = mapped_column(Numeric(12, 4))
    z_kurtosis: Mapped[float] = mapped_column(Numeric(12, 4))
    x_kurtosis: Mapped[float] = mapped_column(Numeric(12, 4))
    z_crest_factor: Mapped[float] = mapped_column(Numeric(12, 4))
    x_crest_factor: Mapped[float] = mapped_column(Numeric(12, 4))
    z_peak_vel_comp_freq_hz: Mapped[float] = mapped_column(Numeric(12, 4))
    x_peak_vel_comp_freq_hz: Mapped[float] = mapped_column(Numeric(12, 4))
    temperature_c: Mapped[float] = mapped_column(Numeric(12, 4))
    rpm: Mapped[float] = mapped_column(Numeric(12, 4))

    features: Mapped[list[float]] = mapped_column(Vector(FEATURE_DIM))

    __table_args__ = (
        CheckConstraint("split IN ('train','holdout')", name="ck_sensor_events_split"),
        # Indice PARCIAL, restrito ao split de treino.
        #
        # O HNSW do pgvector faz pos-filtro: ele encontra os k vizinhos mais
        # proximos e so depois aplica o WHERE. Com um indice sobre a tabela
        # inteira e uma consulta partindo de um evento do holdout, os vizinhos
        # mais proximos sao os proprios registros do holdout (mesma sessao de
        # ensaio) -- todos descartados pelo filtro, e a busca retorna vazio.
        #
        # Como toda busca por similaridade e restrita ao historico por definicao
        # (buscar dentro do holdout seria vazamento), o filtro entra no proprio
        # indice. Resolve a corretude e ainda deixa o indice 5% menor.
        Index(
            "ix_sensor_events_features_hnsw",
            "features",
            postgresql_using="hnsw",
            postgresql_ops={"features": "vector_cosine_ops"},
            postgresql_where=text("split = 'train'"),
        ),
    )


class Document(Base):
    """Documento tecnico da empresa (manual, procedimento, relatorio)."""

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


class DocumentChunk(Base):
    """Trecho de documento com embedding. Carrega a proveniencia que vira citacao."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    ordinal: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))

    document: Mapped[Document] = relationship(back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "ordinal", name="uq_document_chunks_ordinal"),
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class FaultCoverage(Base):
    """Mapa familia de falha -> documento que a cobre.

    E a tabela que sustenta o gate deterministico da SPEC-FEAT-008: sem linha
    aqui, o LLM nao e chamado.
    """

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


class IndexMetadata(Base):
    """Modelo e dimensao usados na indexacao.

    Trocar o modelo de embedding sem reindexar corromperia o indice em silencio;
    com isso gravado, a divergencia e detectada e bloqueada com erro claro.
    """

    __tablename__ = "index_metadata"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
