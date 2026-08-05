"""Contrato do evento de sensor.

Aceita exatamente o JSON de exemplo da secao 2 do enunciado, sem adaptacao. Os
campos extras que aparecem no payload original (`id`, `created_at`, `fault` e as
colunas em unidade imperial) sao aceitos e ignorados -- o integrador nao precisa
filtrar nada antes de enviar.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.features import FEATURE_COLUMNS


class SensorEventIn(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "id": 114387,
                "created_at": "2026-06-01 21:32:53.911176+00:00",
                "z_rms_velocity_mm_s": 1.517,
                "x_rms_velocity_mm_s": 2.0,
                "z_peak_acceleration_g": 0.484,
                "x_peak_acceleration_g": 0.631,
                "z_rms_acceleration_g": 0.09,
                "x_rms_acceleration_g": 0.114,
                "z_high_freq_rms_accel_g": 0.129,
                "x_high_freq_rms_accel_g": 0.147,
                "z_kurtosis": 2.392,
                "x_kurtosis": 2.77,
                "z_crest_factor": 3.747,
                "x_crest_factor": 4.269,
                "z_peak_vel_comp_freq_hz": 61.0,
                "x_peak_vel_comp_freq_hz": 61.0,
                "temperature_c": 24.69,
                "rpm": 1000.0,
            }
        },
    )

    id: int | None = None
    created_at: datetime | None = None

    z_rms_velocity_mm_s: float = Field(description="Velocidade RMS eixo Z (mm/s)")
    x_rms_velocity_mm_s: float = Field(description="Velocidade RMS eixo X (mm/s)")
    z_peak_acceleration_g: float
    x_peak_acceleration_g: float
    z_rms_acceleration_g: float
    x_rms_acceleration_g: float
    z_high_freq_rms_accel_g: float
    x_high_freq_rms_accel_g: float
    z_kurtosis: float
    x_kurtosis: float
    z_crest_factor: float
    x_crest_factor: float
    z_peak_vel_comp_freq_hz: float
    x_peak_vel_comp_freq_hz: float
    temperature_c: float
    rpm: float

    def to_feature_dict(self) -> dict[str, float]:
        """Extrai apenas as colunas que compoem o vetor, na ordem canonica."""
        dados = self.model_dump()
        return {coluna: dados[coluna] for coluna in FEATURE_COLUMNS}


class SensorEventOut(SensorEventIn):
    """Evento vindo do banco, com o rotulo real -- usado nas amostras de demonstracao."""

    raw_fault: str
    fault_family: str
    split: str
