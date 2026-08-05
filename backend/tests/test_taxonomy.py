"""SPEC-FEAT-002 -- criterios de aceite da taxonomia canonica."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.core.taxonomy import (
    FAMILY_DESCRIPTIONS,
    UnknownFaultLabel,
    normalize_fault,
)

CSV_PATH = Path(__file__).resolve().parents[2] / "dados" / "banner.csv"


# --- Aceite: estados nao sao tratados como falha -----------------------------
@pytest.mark.parametrize(
    "raw",
    [
        "normal",
        "normal_2",
        "normal_6",
        "normal_carga",
        "normal_novo",
        "normal_pos_2",
        "normal_carga_3_3",
        "normla_carga_3_3",  # typo
        "new_normal_0",
        "baseline",
        "new_baseline",
        "teste",
        "new_teste",
        "new_tes",
        "normal_novo_teste",
        "acelerando",
        "motor_desligado",
        "motor_desligado_novo",
        "mortor_desligado_novo",  # typo
    ],
)
def test_estados_nao_sao_problema(raw: str) -> None:
    assert normalize_fault(raw).is_problem is False


# --- Aceite: typos convergem para o canonico correto -------------------------
@pytest.mark.parametrize(
    "raw",
    [
        "desbalanceado",
        "desbalanceamento",
        "desbalanceado_3",
        "desbalanceado_carga_2",
        "desbalanceado_1parafuso",
        "desbalanceado_1parafuso_3",
        "desabalanceado_3",  # typo
        "desbanlanceado_carga_3_2",  # typo
        "ddesbalanceado_adxl_0",  # typo
        "dedesbalanceado_adxl_1",  # typo
        "new_desabanceado_1",  # typo
        "new_desbalanceado_antigo_2",
    ],
)
def test_typos_de_desbalanceamento(raw: str) -> None:
    assert normalize_fault(raw).family == "desbalanceamento"


def test_typo_de_cocked_rotor() -> None:
    assert normalize_fault("cockecocked_adxl_0").family == "cocked_rotor"
    assert normalize_fault("cocked_adxl_0").family == "cocked_rotor"


# --- Aceite: sufixos de sessao nao criam familias novas ----------------------
@pytest.mark.parametrize(
    "raw",
    [
        "rolamento_inner",
        "rolamento_inner_2",
        "rolamento_inner_3",
        "rolamento_inner_carga",
        "rolamento_inner_carga_2",
        "rolamento_inner_pos_2",
        "rolamento_inner_adxl_0",
        "new_rolamento_inner_0",
        "rolamento_outer_novo_teste",
        "rolamento_comb_adxl_0",
        "new_rolamento_comb_3",
    ],
)
def test_sufixos_de_sessao_colapsam_na_familia_rolamento(raw: str) -> None:
    assert normalize_fault(raw).family == "rolamento"


def test_subtipo_de_rolamento_e_preservado_no_canonico() -> None:
    """A familia agrega para a documentacao; o canonico guarda a pista afetada."""
    assert normalize_fault("rolamento_inner_carga").canonical == "rolamento_inner"
    assert normalize_fault("rolamento_outer_2").canonical == "rolamento_outer"
    assert normalize_fault("rolamento_ball_adxl_0").canonical == "rolamento_ball"
    assert normalize_fault("new_rolamento_comb_1").canonical == "rolamento_combination"


# --- Aceite: familias distintas nao se fundem --------------------------------
def test_desalinhado_e_desbalanceado_sao_familias_diferentes() -> None:
    desalinhado = normalize_fault("desalinhado")
    desbalanceado = normalize_fault("desbalanceado")
    assert desalinhado.family == "desalinhamento"
    assert desbalanceado.family == "desbalanceamento"
    assert desalinhado.family != desbalanceado.family


def test_cocked_e_eccentric_sao_familias_diferentes() -> None:
    assert normalize_fault("new_cocked_0").family == "cocked_rotor"
    assert normalize_fault("new_eccentric_0").family == "eccentric_rotor"
    assert normalize_fault("eccentric_2_pos_2").family == "eccentric_rotor"


def test_polia_correia_e_ventoinha_sao_distintas() -> None:
    familias = {
        normalize_fault("polia_2").family,
        normalize_fault("correia_2").family,
        normalize_fault("ventoinha_adxl_0").family,
    }
    assert familias == {"polia", "correia", "ventoinha"}


def test_falta_fase() -> None:
    resultado = normalize_fault("new_falta_fase_0")
    assert resultado.family == "falta_fase"
    assert resultado.is_problem is True


# --- Aceite: rotulo desconhecido e erro, nao silencio ------------------------
@pytest.mark.parametrize("raw", ["xpto_999", "", "   ", "falha_inventada"])
def test_rotulo_desconhecido_levanta(raw: str) -> None:
    with pytest.raises(UnknownFaultLabel):
        normalize_fault(raw)


# --- Aceite: rotulo bruto e sempre preservado --------------------------------
def test_raw_e_preservado() -> None:
    assert normalize_fault("ddesbalanceado_adxl_0").raw == "ddesbalanceado_adxl_0"


# --- Aceite: cobertura total dos rotulos do dataset --------------------------
@pytest.mark.skipif(not CSV_PATH.exists(), reason="dados/banner.csv ausente")
def test_cobre_todos_os_rotulos_do_dataset() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        rotulos = {row["fault"] for row in csv.DictReader(handle)}

    assert len(rotulos) == 151, "o dataset mudou; revise a taxonomia"

    falhas = []
    familias = set()
    for rotulo in rotulos:
        try:
            familias.add(normalize_fault(rotulo).family)
        except UnknownFaultLabel:
            falhas.append(rotulo)

    assert not falhas, f"rotulos sem regra na taxonomia: {sorted(falhas)}"
    assert familias == set(FAMILY_DESCRIPTIONS), "familia sem descricao documentada"


def test_toda_familia_tem_descricao() -> None:
    assert all(descricao.strip() for descricao in FAMILY_DESCRIPTIONS.values())
