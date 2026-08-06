"""Contratos de ingestao de leituras.

A secao 2 do enunciado descreve o fluxo real: os sensores enviam leituras
continuamente para o banco corporativo. Este endpoint e a porta de entrada desse
fluxo -- o `/predict` apenas consulta, nao alimenta.

O payload aceito e exatamente o JSON de exemplo do enunciado, incluindo `fault`,
`id`, `created_at` e as colunas em unidade imperial.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.features import METRIC_COLUMNS


class LeituraIn(BaseModel):
    """Uma leitura de sensor, no formato que o coletor da planta produz."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "id": 114387,
                "created_at": "2026-06-01 21:32:53.911176+00:00",
                "z_rms_velocity_in_s": 0.0597,
                "z_rms_velocity_mm_s": 1.517,
                "temperature_f": 76.44,
                "temperature_c": 24.69,
                "x_rms_velocity_in_s": 0.0787,
                "x_rms_velocity_mm_s": 2.0,
                "z_peak_acceleration_g": 0.484,
                "x_peak_acceleration_g": 0.631,
                "z_peak_vel_comp_freq_hz": 61.0,
                "x_peak_vel_comp_freq_hz": 61.0,
                "z_rms_acceleration_g": 0.09,
                "x_rms_acceleration_g": 0.114,
                "z_kurtosis": 2.392,
                "x_kurtosis": 2.77,
                "z_crest_factor": 3.747,
                "x_crest_factor": 4.269,
                "z_peak_velocity_in_s": 0.0844,
                "z_peak_velocity_mm_s": 2.146,
                "x_peak_velocity_in_s": 0.1113,
                "x_peak_velocity_mm_s": 2.829,
                "z_high_freq_rms_accel_g": 0.129,
                "x_high_freq_rms_accel_g": 0.147,
                "fault": "cocked_rotor_2",
                "rpm": 1000.0,
            }
        },
    )

    id: int | None = Field(
        default=None,
        description="Identificador do coletor. Reenviar o mesmo id atualiza o registro.",
    )
    created_at: datetime | None = Field(
        default=None, description="Momento da leitura. Omitir usa o horario de chegada."
    )
    fault: str | None = Field(
        default=None,
        description=(
            "Condicao anotada pelo operador. Quando ausente, a leitura e gravada "
            "como nao anotada: entra no historico para registro, mas nao participa "
            "da votacao de similaridade -- nao ha rotulo para votar."
        ),
    )

    # Colunas metricas. As imperiais do payload original sao aceitas e ignoradas:
    # sao conversao exata das metricas (ver core/features).
    z_rms_velocity_mm_s: float
    x_rms_velocity_mm_s: float
    z_peak_velocity_mm_s: float | None = None
    x_peak_velocity_mm_s: float | None = None
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

    def metricas(self) -> dict[str, float]:
        """Colunas persistidas, com as derivadas calculadas quando ausentes."""
        dados = self.model_dump()
        # `peak_velocity` e derivada do RMS (razao sqrt(2), ver core/features).
        # Se o coletor nao enviar, o valor e reconstruido para nao gravar nulo.
        raiz_de_dois = 1.414214
        if dados.get("z_peak_velocity_mm_s") is None:
            dados["z_peak_velocity_mm_s"] = dados["z_rms_velocity_mm_s"] * raiz_de_dois
        if dados.get("x_peak_velocity_mm_s") is None:
            dados["x_peak_velocity_mm_s"] = dados["x_rms_velocity_mm_s"] * raiz_de_dois
        return {coluna: float(dados[coluna]) for coluna in METRIC_COLUMNS}


class IngestRequest(BaseModel):
    """Uma leitura ou um lote."""

    model_config = ConfigDict(extra="forbid")

    leituras: list[LeituraIn] = Field(min_length=1, max_length=1000)
    analisar: bool = Field(
        default=False,
        description=(
            "Quando verdadeiro, devolve tambem o diagnostico da ultima leitura do "
            "lote. Util para o coletor decidir se abre um chamado."
        ),
    )


class LeituraGravada(BaseModel):
    id: int
    condicao_bruta: str | None
    condicao_canonica: str | None
    familia: str | None
    e_problema: bool | None
    anotada: bool
    ja_existia: bool


class IngestResponse(BaseModel):
    gravadas: int
    anotadas: int = Field(description="Leituras com condicao informada pelo operador")
    atualizadas: int = Field(description="Leituras que ja existiam e foram sobrescritas")
    leituras: list[LeituraGravada]
    rotulos_desconhecidos: list[str] = Field(
        default_factory=list,
        description=(
            "Rotulos que nao casam com a taxonomia. A leitura e gravada como nao "
            "anotada em vez de recusada -- perder o dado do sensor por causa de um "
            "rotulo novo seria pior que grava-lo sem classificacao."
        ),
    )
