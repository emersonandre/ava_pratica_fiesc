"""Relatorio do conjunto de dados.

    python manage.py report dataset

Contagens, periodo, distribuicao por familia e o corte temporal que separa
historico de conjunto de teste. Evidencia da SPEC-FEAT-004.
"""

from __future__ import annotations

from sqlalchemy import func, select

from app.core.features import FEATURE_COLUMNS, METRIC_COLUMNS, REDUNDANT_COLUMNS
from app.core.taxonomy import FAMILY_DESCRIPTIONS, PROBLEM_FAMILIES
from app.database import session_scope
from app.models import SensorEvent
from app.settings import PROJECT_ROOT

SAIDA = PROJECT_ROOT / "backend" / "docs" / "analise" / "dataset.md"


def _milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def run() -> int:
    with session_scope() as session:
        total = session.scalar(select(func.count()).select_from(SensorEvent)) or 0

        por_split = session.execute(
            select(
                SensorEvent.split,
                func.count(),
                func.min(SensorEvent.created_at),
                func.max(SensorEvent.created_at),
            ).group_by(SensorEvent.split)
        ).all()

        por_familia = session.execute(
            select(
                SensorEvent.fault_family,
                func.count(),
                func.count().filter(SensorEvent.split == "train"),
                func.count().filter(SensorEvent.split == "holdout"),
                func.count(func.distinct(SensorEvent.canonical_fault)),
            )
            .group_by(SensorEvent.fault_family)
            .order_by(func.count().desc())
        ).all()

        rotulos_brutos = session.scalar(
            select(func.count(func.distinct(SensorEvent.raw_fault)))
        )
        problemas = session.scalar(
            select(func.count()).select_from(SensorEvent).where(SensorEvent.is_problem)
        )

        rpm = session.execute(
            select(SensorEvent.rpm, func.count())
            .group_by(SensorEvent.rpm)
            .order_by(SensorEvent.rpm)
        ).all()

    linhas: list[str] = [
        "# Conjunto de dados",
        "",
        "> Gerado por `python manage.py report dataset`.",
        "> Evidencia da [SPEC-FEAT-004](../SPEC-FEAT-004/spec.md).",
        "",
        "## Volume",
        "",
        "| | |",
        "| --- | ---: |",
        f"| Leituras | {_milhar(total)} |",
        f"| Rotulos brutos distintos | {rotulos_brutos} |",
        f"| Familias canonicas | {len(por_familia)} |",
        f"| Familias que representam problema | {len(PROBLEM_FAMILIES)} |",
        f"| Leituras classificadas como problema | {_milhar(problemas or 0)} "
        f"({100 * (problemas or 0) / total:.1f}%) |",
        "",
        "## Corte temporal",
        "",
        "Todo rotulo com prefixo `new_` foi coletado entre 10 e 16 de junho; todo o",
        "restante e de ate 09 de junho. O conjunto de teste sai desse corte natural,",
        "sem sorteio.",
        "",
        "Sorteio aleatorio seria um erro grave aqui: amostras da mesma sessao de ensaio",
        "foram coletadas com segundos de diferenca e cairiam dos dois lados. O vizinho",
        "mais proximo de uma leitura de teste seria praticamente ela mesma, e a acuracia",
        "sairia inflada e falsa.",
        "",
        "| Split | Leituras | Periodo |",
        "| --- | ---: | --- |",
    ]

    for split, quantidade, inicio, fim in sorted(por_split):
        periodo = f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}" if inicio else "—"
        linhas.append(f"| `{split}` | {_milhar(quantidade)} | {periodo} |")

    linhas += [
        "",
        "## Distribuicao por familia",
        "",
        "| Familia | Descricao | Problema | Total | Treino | Teste | Subtipos |",
        "| --- | --- | :---: | ---: | ---: | ---: | ---: |",
    ]

    sem_teste = []
    so_no_teste = []
    for familia, total_f, treino, teste, subtipos in por_familia:
        if familia is None:
            continue
        marca = "sim" if familia in PROBLEM_FAMILIES else "nao"
        linhas.append(
            f"| `{familia}` | {FAMILY_DESCRIPTIONS.get(familia, '')} | {marca} "
            f"| {_milhar(total_f)} | {_milhar(treino)} | {_milhar(teste)} | {subtipos} |"
        )
        if familia in PROBLEM_FAMILIES:
            if teste == 0:
                sem_teste.append(familia)
            if treino == 0:
                so_no_teste.append(familia)

    linhas += [
        "",
        "### Familias ausentes de um dos lados",
        "",
        "O corte temporal e honesto, mas nao e equilibrado -- e isso tem consequencia",
        "direta no que o sistema consegue fazer.",
        "",
    ]

    if so_no_teste:
        linhas += [
            "**Sem historico** — aparecem no conjunto de teste e nao no de treino. Nenhuma",
            "busca por similaridade poderia acerta-las; o comportamento correto e recusar:",
            "",
            *[f"- `{f}`" for f in so_no_teste],
            "",
        ]

    if sem_teste:
        linhas += [
            "**Sem leitura de teste** — existem no historico, mas nao no periodo reservado",
            "para avaliacao. Nao podem ser demonstradas, e a interface nao as oferece:",
            "",
            *[f"- `{f}`" for f in sem_teste],
            "",
        ]

    linhas += [
        "## Regimes de rotacao",
        "",
        "| RPM | Leituras |",
        "| ---: | ---: |",
    ]
    for valor, quantidade in rpm:
        linhas.append(f"| {float(valor):.0f} | {_milhar(quantidade)} |")

    linhas += [
        "",
        "Vibracao escala com a rotacao (F = m·r·ω², conforme o Doc3), entao o RPM entra",
        "no vetor de features: comparar uma leitura a 2000 rpm com outra a 500 rpm sem",
        "esse eixo produziria vizinho sem sentido fisico.",
        "",
        "## Colunas",
        "",
        f"O CSV traz 24 colunas numericas. {len(FEATURE_COLUMNS)} entram no vetor de",
        f"similaridade, {len(METRIC_COLUMNS)} sao persistidas para exibicao e",
        f"{len(REDUNDANT_COLUMNS)} sao descartadas por redundancia.",
        "",
        "### No vetor de similaridade",
        "",
        *[f"- `{coluna}`" for coluna in FEATURE_COLUMNS],
        "",
        "### Descartadas",
        "",
        "Conversao de unidade — correlacao >= 0,999999 com a coluna metrica mantida:",
        "",
        *[f"- `{c}`" for c in REDUNDANT_COLUMNS if c.endswith(("_in_s", "_f"))],
        "",
        "Coluna derivada — `peak_velocity` e o RMS multiplicado por sqrt(2), calculado",
        "pelo firmware assumindo sinal senoidal. Correlacao 1,000000; nao carrega",
        "informacao alem do RMS:",
        "",
        *[f"- `{c}`" for c in REDUNDANT_COLUMNS if c.endswith("_mm_s")],
        "",
        "Detalhamento da auditoria de redundancia em",
        "[SPEC-FEAT-003](../SPEC-FEAT-003/spec.md).",
        "",
    ]

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(linhas), encoding="utf-8")
    print(f"  dataset.md: {_milhar(total)} leituras, {len(por_familia)} familias")
    return 0
