"""Gera backend/docs/analise/taxonomia.md a partir do dataset real.

    python -m app.scripts.report_taxonomy

O relatorio e a evidencia auditavel da SPEC-FEAT-002: mostra cada rotulo bruto,
para onde ele foi mapeado e quantos registros isso representa.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from app.config import PROJECT_ROOT, get_settings
from app.core.taxonomy import (
    FAMILY_DESCRIPTIONS,
    PROBLEM_FAMILIES,
    TOKEN_TYPOS,
    UnknownFaultLabel,
    normalize_fault,
)

OUTPUT = PROJECT_ROOT / "backend" / "docs" / "analise" / "taxonomia.md"


def main() -> int:
    settings = get_settings()
    counts: Counter[str] = Counter()
    periods: dict[str, list[str]] = defaultdict(lambda: ["", ""])

    with settings.csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            label = row["fault"]
            counts[label] += 1
            day = row["created_at"][:10]
            window = periods[label]
            window[0] = day if not window[0] or day < window[0] else window[0]
            window[1] = day if not window[1] or day > window[1] else window[1]

    rows = []
    unknown = []
    by_family: Counter[str] = Counter()
    by_canonical: Counter[str] = Counter()

    for label, total in counts.items():
        try:
            result = normalize_fault(label)
        except UnknownFaultLabel:
            unknown.append(label)
            continue
        by_family[result.family] += total
        by_canonical[result.canonical] += total
        rows.append((label, result.canonical, result.family, result.is_problem, total))

    rows.sort(key=lambda item: (item[2], item[1], -item[4]))
    total_records = sum(counts.values())
    problem_records = sum(n for family, n in by_family.items() if family in PROBLEM_FAMILIES)

    lines: list[str] = [
        "# Taxonomia canonica de falhas",
        "",
        "> Gerado por `python -m app.scripts.report_taxonomy` a partir de `dados/banner.csv`.",
        "> Evidencia da [SPEC-FEAT-002](../SPEC-FEAT-002/spec.md).",
        "",
        "## Resumo",
        "",
        "| | |",
        "| --- | --- |",
        f"| Registros | {total_records:,} |".replace(",", "."),
        f"| Rotulos brutos distintos | {len(counts)} |",
        f"| Rotulos canonicos | {len(by_canonical)} |",
        f"| Familias | {len(by_family)} |",
        f"| Familias de problema | {len(PROBLEM_FAMILIES)} |",
        f"| Registros classificados como problema | {problem_records:,} "
        f"({100 * problem_records / total_records:.1f}%) |".replace(",", "."),
        f"| Rotulos sem regra | {len(unknown)} |",
        "",
    ]

    if unknown:
        lines += ["> **Atencao:** rotulos sem regra: " + ", ".join(sorted(unknown)), ""]

    lines += [
        "## Familias",
        "",
        "| Familia | Descricao | Problema | Registros | % |",
        "| --- | --- | :---: | ---: | ---: |",
    ]
    for family, total in by_family.most_common():
        is_problem = "sim" if family in PROBLEM_FAMILIES else "nao"
        pct = 100 * total / total_records
        lines.append(
            f"| `{family}` | {FAMILY_DESCRIPTIONS[family]} | {is_problem} "
            f"| {total:,} | {pct:.1f}% |".replace(",", ".")
        )

    lines += [
        "",
        "## Erros de digitacao corrigidos",
        "",
        "Correcoes aplicadas no nivel do token, todas confirmadas no dataset.",
        "",
        "| Token errado | Token correto |",
        "| --- | --- |",
    ]
    for wrong, right in sorted(TOKEN_TYPOS.items()):
        lines.append(f"| `{wrong}` | `{right}` |")

    lines += [
        "",
        "## Matriz completa: rotulo bruto -> canonico",
        "",
        f"Os {len(rows)} rotulos brutos do dataset, agrupados por familia.",
        "",
        "| Rotulo bruto | Canonico | Familia | Problema | Registros | Periodo |",
        "| --- | --- | --- | :---: | ---: | --- |",
    ]
    for label, canonical, family, is_problem, total in rows:
        start, end = periods[label]
        period = start if start == end else f"{start} a {end}"
        lines.append(
            f"| `{label}` | `{canonical}` | `{family}` | {'sim' if is_problem else 'nao'} "
            f"| {total:,} | {period} |".replace(",", ".")
        )

    lines.append("")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUTPUT.relative_to(PROJECT_ROOT)}: {len(rows)} rotulos, {len(by_family)} familias")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
