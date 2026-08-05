"""SPEC-FEAT-003 -- criterios de aceite do vetor de features."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.core.features import (
    FEATURE_COLUMNS,
    FEATURE_DIM,
    METRIC_COLUMNS,
    REDUNDANT_COLUMNS,
    MissingFeatureError,
    build_feature_frame,
    fit_scaler,
    to_vector,
    transform,
)


def _amostra(n: int = 50, semente: int = 0) -> pd.DataFrame:
    gerador = np.random.default_rng(semente)
    dados = {coluna: gerador.normal(10, 3, n) for coluna in METRIC_COLUMNS}
    dados["rpm"] = gerador.choice([0.0, 500.0, 1000.0, 2000.0], n)
    return pd.DataFrame(dados)


# --- Aceite: vetor final sem duplicidade de grandeza -------------------------
def test_nenhuma_coluna_imperial_no_vetor() -> None:
    assert not [c for c in FEATURE_COLUMNS if c.endswith("_in_s")]
    assert "temperature_f" not in FEATURE_COLUMNS


def test_pico_de_velocidade_fora_do_vetor() -> None:
    """`peak_velocity` e derivada de `rms_velocity` (razao sqrt(2))."""
    assert "z_peak_velocity_mm_s" not in FEATURE_COLUMNS
    assert "x_peak_velocity_mm_s" not in FEATURE_COLUMNS


def test_colunas_derivadas_seguem_persistidas_para_exibicao() -> None:
    assert "z_peak_velocity_mm_s" in METRIC_COLUMNS
    assert "x_peak_velocity_mm_s" in METRIC_COLUMNS


def test_redundantes_e_features_nao_se_sobrepoem() -> None:
    assert not set(REDUNDANT_COLUMNS) & set(FEATURE_COLUMNS)


def test_dimensao_bate_com_as_colunas() -> None:
    assert FEATURE_DIM == len(FEATURE_COLUMNS) == 16


# --- Aceite: ordem estavel ---------------------------------------------------
def test_ordem_do_vetor_e_a_mesma_na_ingestao_e_na_inferencia() -> None:
    df = _amostra()
    scaler = fit_scaler(df)

    do_frame = transform(scaler, df.head(1))[0]
    do_payload = to_vector(scaler, df.head(1).iloc[0].to_dict())

    np.testing.assert_allclose(do_frame, do_payload)


def test_frame_respeita_a_ordem_canonica() -> None:
    assert tuple(build_feature_frame(_amostra()).columns) == FEATURE_COLUMNS


# --- Aceite: scaler reutilizado, nao reajustado ------------------------------
def test_scaler_nao_se_reajusta_no_dado_de_inferencia() -> None:
    treino = _amostra(semente=1)
    scaler = fit_scaler(treino)
    media_antes = scaler.mean_.copy()

    to_vector(scaler, _amostra(n=1, semente=99).iloc[0].to_dict())

    np.testing.assert_array_equal(scaler.mean_, media_antes)


def test_motor_desligado_fica_fora_do_ajuste() -> None:
    df = _amostra(n=100)
    df.loc[:49, "rpm"] = 0.0
    parado = df["rpm"] == 0.0

    com_tudo = fit_scaler(df)
    sem_parado = fit_scaler(df, exclude_mask=parado)

    indice_rpm = FEATURE_COLUMNS.index("rpm")
    assert sem_parado.mean_[indice_rpm] > com_tudo.mean_[indice_rpm]


# --- Aceite: erro util em entrada incompleta ---------------------------------
def test_coluna_ausente_nomeia_o_campo() -> None:
    df = _amostra().drop(columns=["z_kurtosis"])
    with pytest.raises(MissingFeatureError, match="z_kurtosis"):
        build_feature_frame(df)


def test_payload_incompleto_nomeia_o_campo() -> None:
    df = _amostra()
    scaler = fit_scaler(df)
    payload = df.iloc[0].to_dict()
    del payload["rpm"]

    with pytest.raises(MissingFeatureError, match="rpm"):
        to_vector(scaler, payload)


# --- Aceite: sem NaN no vetor final ------------------------------------------
def test_nulo_e_reportado_em_vez_de_propagado() -> None:
    df = _amostra()
    df.loc[3, "x_kurtosis"] = np.nan
    with pytest.raises(MissingFeatureError, match="x_kurtosis"):
        build_feature_frame(df)


def test_scaler_sem_registro_restante_levanta() -> None:
    df = _amostra(n=10)
    with pytest.raises(ValueError, match="nenhum registro"):
        fit_scaler(df, exclude_mask=pd.Series(True, index=df.index))
