"""Normalizacao dos rotulos de falha anotados manualmente pelo operador.

A coluna `fault` do banner.csv tem 151 valores distintos que colapsam em 14 familias.
O ruido vem de tres fontes, tratadas separadamente aqui:

1. Sufixos/prefixos de sessao de ensaio (`_2`, `_carga`, `_adxl_0`, `_pos_2`, `new_`...)
   -- indicam repeticao do ensaio, mudanca de carga ou troca de acelerometro, nao uma
   falha diferente.
2. Erros de digitacao do operador (`mortor_desligado_novo`, `normla_carga_3_3`,
   `cockecocked_adxl_0`, `ddesbalanceado_adxl_0`...).
3. Estados operacionais que nao sao problemas (`normal`, `baseline`, `teste`,
   `acelerando`, `motor_desligado`), conforme a secao 6 do enunciado.

A normalizacao e deterministica e lexica -- nao usa fuzzy matching. Um `difflib`
cego aproximaria `desalinhado` de `desbalanceado`: distancia pequena, falhas
completamente diferentes. Os erros de digitacao sao poucos e conhecidos, entao
viram um dicionario explicito, revisavel e testavel.

Rotulo que nao case com nenhuma regra levanta `UnknownFaultLabel`. Falhar alto na
ingestao e melhor que criar uma familia `unknown` que envenena silenciosamente as
contagens de similaridade e o mapa de cobertura documental.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

# ---------------------------------------------------------------------------
# 1. Tokens de sessao de ensaio -- descartados
# ---------------------------------------------------------------------------
# `new`    -> lote de coleta de 10 a 16/jun (vira o split de holdout)
# `carga`  -> ensaio com carga aplicada
# `adxl`   -> coleta com acelerometro ADXL
# `pos`    -> reposicionamento do sensor
# `novo`   / `antigo` -> versao do ensaio
# numerico -> indice de repeticao
SESSION_TOKENS: Final[frozenset[str]] = frozenset(
    {"new", "novo", "antigo", "carga", "adxl", "pos"}
)

# `teste` tambem e um estado valido por si so. E descartado como token de sessao,
# mas se o rotulo inteiro se resumir a ele, o resultado e o estado `teste`.
TEST_TOKENS: Final[frozenset[str]] = frozenset({"teste", "tes"})

NUMERIC_RE: Final = re.compile(r"^\d+$")

# ---------------------------------------------------------------------------
# 2. Erros de digitacao do operador -- todos confirmados no dataset
# ---------------------------------------------------------------------------
TOKEN_TYPOS: Final[dict[str, str]] = {
    # motor_desligado
    "mortor": "motor",
    # normal
    "normla": "normal",
    # cocked_rotor
    "cockecocked": "cocked",
    # desbalanceado (cinco grafias erradas distintas)
    "desabalanceado": "desbalanceado",
    "desabanceado": "desbalanceado",
    "ddesbalanceado": "desbalanceado",
    "dedesbalanceado": "desbalanceado",
    "desbanlanceado": "desbalanceado",
    # forma substantivada usada em alguns registros
    "desbalanceamento": "desbalanceado",
    # abreviacao de `combination`
    "comb": "combination",
}

# ---------------------------------------------------------------------------
# 3. Nucleo do rotulo -> (canonico, familia, e problema?)
# ---------------------------------------------------------------------------
# `canonical` preserva o subtipo tecnico (qual pista do rolamento falhou, qual a
# severidade do desbalanceamento). `family` e o nivel em que a documentacao existe
# e em que a cobertura e avaliada.
NORMAL_STATES: Final[dict[str, str]] = {
    "normal": "normal",
    "baseline": "baseline",
    "acelerando": "acelerando",
    "motor_desligado": "motor_desligado",
    "teste": "teste",
}

CORE_MAP: Final[dict[str, tuple[str, str]]] = {
    # --- rolamentos: subtipo importa tecnicamente, documentacao e por familia ---
    "rolamento_inner": ("rolamento_inner", "rolamento"),
    "rolamento_outer": ("rolamento_outer", "rolamento"),
    "rolamento_ball": ("rolamento_ball", "rolamento"),
    "rolamento_combination": ("rolamento_combination", "rolamento"),
    # --- desbalanceamento ---
    "desbalanceado": ("desbalanceamento", "desbalanceamento"),
    "desbalanceado_1parafuso": ("desbalanceamento_1parafuso", "desbalanceamento"),
    # --- desalinhamento ---
    "desalinhado": ("desalinhamento", "desalinhamento"),
    # --- geometria do rotor ---
    "cocked_rotor": ("cocked_rotor", "cocked_rotor"),
    "eccentric_rotor": ("eccentric_rotor", "eccentric_rotor"),
    # --- transmissao ---
    "polia": ("polia", "polia"),
    "correia": ("correia", "correia"),
    "ventoinha": ("ventoinha", "ventoinha"),
    # --- eletrico ---
    "falta_fase": ("falta_fase", "falta_fase"),
}

# Formas abreviadas que aparecem sem o substantivo (`new_cocked_0`, `eccentric_adxl_0`).
CORE_ALIASES: Final[dict[str, str]] = {
    "cocked": "cocked_rotor",
    "eccentric": "eccentric_rotor",
}

# Familias que representam problema (universo da prescricao).
PROBLEM_FAMILIES: Final[frozenset[str]] = frozenset(
    {family for _, family in CORE_MAP.values()}
)

# Familias que representam estado do sistema (secao 6 do enunciado).
STATE_FAMILIES: Final[frozenset[str]] = frozenset(NORMAL_STATES.values())

FAMILY_DESCRIPTIONS: Final[dict[str, str]] = {
    "rolamento": "Defeito em rolamento (pista interna, externa, esferas ou combinado)",
    "desbalanceamento": "Distribuicao desigual de massa no rotor",
    "desalinhamento": "Eixos do motor e da carga fora de alinhamento",
    "cocked_rotor": "Rotor inclinado em relacao ao eixo de rotacao",
    "eccentric_rotor": "Centro geometrico do rotor deslocado do centro de rotacao",
    "polia": "Defeito em polia (excentricidade, desbalanceamento, desgaste)",
    "correia": "Defeito no sistema de transmissao por correia",
    "ventoinha": "Defeito na ventoinha do motor",
    "falta_fase": "Operacao com falta de fase na alimentacao eletrica",
    "normal": "Operacao normal",
    "baseline": "Coleta de referencia",
    "teste": "Coleta de teste",
    "acelerando": "Transiente de aceleracao",
    "motor_desligado": "Motor parado",
}


class UnknownFaultLabel(ValueError):
    """Rotulo que nao casa com nenhuma regra da taxonomia."""

    def __init__(self, raw: str, core: str) -> None:
        super().__init__(
            f"Rotulo desconhecido: {raw!r} (nucleo extraido: {core!r}). "
            "Adicione a regra em app/core/taxonomy.py antes de reingerir."
        )
        self.raw = raw
        self.core = core


@dataclass(frozen=True, slots=True)
class FaultLabel:
    raw: str
    canonical: str
    family: str
    is_problem: bool


def _tokenize(raw: str) -> list[str]:
    """Quebra o rotulo, corrige grafia e descarta tokens de sessao de ensaio."""
    tokens = [token for token in raw.strip().lower().split("_") if token]
    tokens = [TOKEN_TYPOS.get(token, token) for token in tokens]
    return [
        token
        for token in tokens
        if token not in SESSION_TOKENS
        and token not in TEST_TOKENS
        and not NUMERIC_RE.match(token)
    ]


def normalize_fault(raw: str) -> FaultLabel:
    """Converte um rotulo bruto em rotulo canonico, familia e flag de problema."""
    if raw is None or not str(raw).strip():
        raise UnknownFaultLabel(str(raw), "")

    tokens = _tokenize(str(raw))

    # Rotulo composto so por tokens de sessao/teste: e uma coleta de teste.
    if not tokens:
        return FaultLabel(raw=raw, canonical="teste", family="teste", is_problem=False)

    core = "_".join(tokens)
    core = CORE_ALIASES.get(core, core)

    if core in NORMAL_STATES:
        state = NORMAL_STATES[core]
        return FaultLabel(raw=raw, canonical=state, family=state, is_problem=False)

    if core in CORE_MAP:
        canonical, family = CORE_MAP[core]
        return FaultLabel(raw=raw, canonical=canonical, family=family, is_problem=True)

    raise UnknownFaultLabel(raw, core)


def is_problem_family(family: str) -> bool:
    return family in PROBLEM_FAMILIES
