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
    #
    # Nulos sao permitidos porque o chao de fabrica envia leitura antes de haver
    # anotacao: o sensor mede continuamente, o operador classifica depois (ou
    # nunca). Uma leitura sem rotulo entra no historico para registro, mas nao
    # pode votar numa busca por similaridade -- nao ha rotulo para votar.
    raw_fault: Mapped[str | None] = mapped_column(String(80), nullable=True)
    canonical_fault: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    fault_family: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    is_problem: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # `train`    ate 09/jun, base historica do dataset entregue
    # `holdout`  rotulos new_*, de 10 a 16/jun -- reservado para avaliacao
    # `producao` leituras recebidas pela API depois da entrega
    #
    # O corte train/holdout e temporal e natural, sem sorteio: evita que amostras
    # da mesma sessao de ensaio (coletadas com segundos de diferenca) caiam dos
    # dois lados e inflem a acuracia medida.
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
        CheckConstraint(
            "split IN ('train','holdout','producao')", name="ck_sensor_events_split"
        ),
        # Indice PARCIAL, cobrindo exatamente o que pode ser vizinho.
        #
        # Duas exclusoes, por motivos diferentes:
        #
        # 1. `holdout` fica de fora porque buscar la seria vazamento -- e o
        #    conjunto reservado para medir o desempenho.
        # 2. Leitura sem rotulo fica de fora porque nao tem como votar: a
        #    similaridade decide pela condicao anotada dos vizinhos.
        #
        # O filtro precisa estar no INDICE, nao so na consulta. O HNSW do pgvector
        # faz pos-filtro: encontra os k vizinhos e so depois aplica o WHERE. Com um
        # indice sobre a tabela inteira e uma consulta partindo de um evento do
        # holdout, os vizinhos mais proximos sao os proprios registros do holdout
        # (mesma sessao de ensaio) -- todos descartados pelo filtro, e a busca
        # retorna VAZIO. Aconteceu na pratica durante a implementacao.
        Index(
            "ix_sensor_events_features_hnsw",
            "features",
            postgresql_using="hnsw",
            postgresql_ops={"features": "vector_cosine_ops"},
            postgresql_where=text("split <> 'holdout' AND fault_family IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<SensorEvent id={self.id} familia={self.fault_family} split={self.split}>"
