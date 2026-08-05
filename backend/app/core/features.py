"""Vetor de features usado na busca por similaridade.

O dataset traz 24 colunas numericas, mas varias sao a mesma grandeza fisica em
outra unidade. Auditoria sobre os 166.796 registros (ver docs/analise/features.md):

    z_rms_velocity_in_s  x  z_rms_velocity_mm_s   corr=0.999999  razao=25.4114
    x_rms_velocity_in_s  x  x_rms_velocity_mm_s   corr=0.999999  razao=25.4079
    z_peak_velocity_in_s x  z_peak_velocity_mm_s  corr=1.000000  razao=25.4081
    x_peak_velocity_in_s x  x_peak_velocity_mm_s  corr=1.000000  razao=25.4056
    temperature_f        x  temperature_c         corr=0.999999  (relacao afim)

Manter as duas versoes daria peso dobrado a velocidade e a temperatura no calculo
de distancia, enviesando o vizinho mais proximo. Ficam as colunas metricas, que
inclusive tem mais precisao armazenada (mm/s tem 3.568 valores distintos contra
1.954 em in/s -- o valor imperial e o arredondado).
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Ordem estavel: define o layout do vetor gravado no banco. Alterar esta tupla
# exige reingerir os dados e recriar o indice.
FEATURE_COLUMNS: Final[tuple[str, ...]] = (
    # Velocidade de vibracao -- severidade global (norma ISO 10816)
    "z_rms_velocity_mm_s",
    "x_rms_velocity_mm_s",
    "z_peak_velocity_mm_s",
    "x_peak_velocity_mm_s",
    # Aceleracao -- sensivel a impacto e alta frequencia
    "z_peak_acceleration_g",
    "x_peak_acceleration_g",
    "z_rms_acceleration_g",
    "x_rms_acceleration_g",
    "z_high_freq_rms_accel_g",
    "x_high_freq_rms_accel_g",
    # Forma do sinal -- discrimina impacto (rolamento) de desbalanceamento
    "z_kurtosis",
    "x_kurtosis",
    "z_crest_factor",
    "x_crest_factor",
    # Frequencia da componente dominante -- harmonica da rotacao (1x, 2x...)
    "z_peak_vel_comp_freq_hz",
    "x_peak_vel_comp_freq_hz",
    # Contexto operacional
    "temperature_c",
    "rpm",
)

FEATURE_DIM: Final[int] = len(FEATURE_COLUMNS)

# Descartadas por serem transformacao linear exata de uma coluna mantida.
REDUNDANT_COLUMNS: Final[tuple[str, ...]] = (
    "z_rms_velocity_in_s",
    "x_rms_velocity_in_s",
    "z_peak_velocity_in_s",
    "x_peak_velocity_in_s",
    "temperature_f",
)

SCALER_FILENAME: Final[str] = "scaler.joblib"


class MissingFeatureError(ValueError):
    """Payload de inferencia sem uma coluna obrigatoria."""


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Seleciona e ordena as colunas de feature, validando ausencia e nulos."""
    faltando = [column for column in FEATURE_COLUMNS if column not in df.columns]
    if faltando:
        raise MissingFeatureError(f"colunas ausentes: {faltando}")

    frame = df.loc[:, list(FEATURE_COLUMNS)].astype("float64")

    if frame.isna().any().any():
        nulos = frame.columns[frame.isna().any()].tolist()
        linhas = frame.index[frame.isna().any(axis=1)][:5].tolist()
        raise MissingFeatureError(
            f"valores nulos nas colunas {nulos} (primeiras linhas afetadas: {linhas})"
        )
    return frame


def fit_scaler(df: pd.DataFrame, *, exclude_mask: pd.Series | None = None) -> StandardScaler:
    """Ajusta o StandardScaler.

    `exclude_mask` marca registros que nao devem influenciar media e desvio --
    na pratica, `motor_desligado` (RPM = 0). Sao estado valido e continuam no
    banco, mas nao representam operacao e distorceriam a escala de RPM.

    StandardScaler e nao min-max: kurtosis e crest factor tem cauda pesada
    (kurtosis vai de 2,0 a 65,5) e min-max deixaria toda a escala refem do outlier.
    """
    treino = df if exclude_mask is None else df.loc[~exclude_mask]
    if treino.empty:
        raise ValueError("nenhum registro restante para ajustar o scaler")
    return StandardScaler().fit(build_feature_frame(treino))


def transform(scaler: StandardScaler, df: pd.DataFrame) -> np.ndarray:
    return scaler.transform(build_feature_frame(df))


def to_vector(scaler: StandardScaler, payload: dict) -> np.ndarray:
    """Converte um JSON de evento (formato da secao 2 do enunciado) em vetor.

    Usa exatamente o mesmo caminho da ingestao -- sem codigo paralelo que possa
    divergir na ordem das colunas.
    """
    faltando = [column for column in FEATURE_COLUMNS if column not in payload]
    if faltando:
        raise MissingFeatureError(f"campos ausentes no payload: {faltando}")
    frame = pd.DataFrame([{column: payload[column] for column in FEATURE_COLUMNS}])
    return transform(scaler, frame)[0]


def scaler_path(artifacts_dir: Path) -> Path:
    return artifacts_dir / SCALER_FILENAME


def save_scaler(scaler: StandardScaler, artifacts_dir: Path) -> Path:
    import joblib

    path = scaler_path(artifacts_dir)
    joblib.dump({"scaler": scaler, "columns": FEATURE_COLUMNS}, path)
    return path


def load_scaler(artifacts_dir: Path) -> StandardScaler:
    import joblib

    path = scaler_path(artifacts_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} nao encontrado. Rode a ingestao (python -m app.scripts.ingest_csv) antes."
        )
    payload = joblib.load(path)
    if tuple(payload["columns"]) != FEATURE_COLUMNS:
        raise ValueError(
            "scaler salvo com outro conjunto de colunas. Reingerir os dados e obrigatorio "
            "para nao misturar layouts de vetor."
        )
    return payload["scaler"]
