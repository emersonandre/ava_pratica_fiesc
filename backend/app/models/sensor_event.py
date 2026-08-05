"""Evento de sensor de vibracao."""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.features import FEATURE_DIM
from app.database.base import Base


class SensorEvent(Base):
    """Um registro do banner.csv, ja normalizado e vetorizado."""

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
        # O HNSW do pgvector faz pos-filtro: encontra os k vizinhos mais proximos
        # e so depois aplica o WHERE. Com um indice sobre a tabela inteira e uma
        # consulta partindo de um evento do holdout, os vizinhos mais proximos sao
        # os proprios registros do holdout (mesma sessao de ensaio) -- todos
        # descartados pelo filtro, e a busca retorna vazio.
        #
        # Como toda busca por similaridade e restrita ao historico por definicao
        # (buscar dentro do holdout seria vazamento), o filtro entra no proprio
        # indice. Resolve a corretude e ainda deixa o indice menor.
        Index(
            "ix_sensor_events_features_hnsw",
            "features",
            postgresql_using="hnsw",
            postgresql_ops={"features": "vector_cosine_ops"},
            postgresql_where=text("split = 'train'"),
        ),
    )

    def __repr__(self) -> str:
        return f"<SensorEvent id={self.id} familia={self.fault_family} split={self.split}>"
