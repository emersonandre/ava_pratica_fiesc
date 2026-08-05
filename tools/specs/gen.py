"""Gera as pastas SPEC-FEAT-XXX a partir dos catálogos.

    python tools/specs/gen.py

Regras:
- `spec.md` é sempre reescrito — o catálogo é a fonte de verdade.
- `tasks.md` e `acceptance.md` preservam os checkboxes já marcados: o texto vem do
  catálogo, o estado (concluído ou não) vem do arquivo existente.
- O índice `README.md` de cada app é recalculado a partir da contagem de checkboxes.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOGS = ["catalog_backend.py", "catalog_frontend.py"]

CHECKBOX_RE = re.compile(r"^- \[([ xX])\] (?:\*\*)?(.+?)(?:\*\*)?$")


@dataclass
class Progress:
    done: int
    total: int

    @property
    def ratio(self) -> float:
        return self.done / self.total if self.total else 0.0


def load_catalog(filename: str):
    path = Path(__file__).parent / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_checked(path: Path) -> set[str]:
    """Retorna o texto dos itens já marcados como concluídos."""
    if not path.exists():
        return set()
    checked = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX_RE.match(line.strip())
        if match and match.group(1).lower() == "x":
            checked.add(match.group(2).strip())
    return checked


def count_checkboxes(path: Path) -> Progress:
    if not path.exists():
        return Progress(0, 0)
    done = total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX_RE.match(line.strip())
        if match:
            total += 1
            done += match.group(1).lower() == "x"
    return Progress(done, total)


def status_symbol(tasks: Progress, acceptance: Progress) -> str:
    if tasks.total and tasks.done == tasks.total and acceptance.done == acceptance.total:
        return "✅"
    if tasks.done or acceptance.done:
        return "🟨"
    return "⬜"


def block(text: str) -> str:
    return text.strip("\n")


def render_spec(feature: dict, module) -> str:
    epic = module.EPICS[feature["epic"]]
    depends = feature["depends"]
    depends_txt = ", ".join(f"`{d}`" for d in depends) if depends else "—"
    return f"""# {feature["id"]} — {feature["title"]}

| | |
| --- | --- |
| **App** | {module.APP} |
| **Épico** | {epic} |
| **Atende** | {feature["atende"]} |
| **Depende de** | {depends_txt} |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

{block(feature["contexto"])}

## Escopo

{block(feature["escopo"])}

## Fora de escopo

{block(feature["fora_escopo"])}

## Decisões técnicas

{block(feature["decisoes"])}

## Contrato

{block(feature["contrato"])}
"""


def render_acceptance(feature: dict, checked: set[str]) -> str:
    lines = [
        f"# {feature['id']} — Critérios de aceite",
        "",
        f"**Feature:** {feature['title']}  ",
        "Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.",
        "",
    ]
    for index, (title, verification) in enumerate(feature["acceptance"], start=1):
        mark = "x" if title in checked else " "
        lines += [
            f"- [{mark}] **{title}**",
            f"  - *Verificação:* {verification}",
            "",
        ]
    return "\n".join(lines)


def render_tasks(feature: dict, checked: set[str]) -> str:
    lines = [
        f"# {feature['id']} — Tarefas",
        "",
        f"**Feature:** {feature['title']}",
        "",
    ]
    for task in feature["tasks"]:
        mark = "x" if task in checked else " "
        lines.append(f"- [{mark}] {task}")
    lines += [
        "",
        "---",
        "",
        f"Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).",
        "",
    ]
    return "\n".join(lines)


def render_index(module, rows: list[dict]) -> str:
    by_epic: dict[str, list[dict]] = {key: [] for key in module.EPICS}
    for row in rows:
        by_epic[row["epic"]].append(row)

    total_tasks = sum(r["tasks"].total for r in rows)
    done_tasks = sum(r["tasks"].done for r in rows)
    done_features = sum(r["symbol"] == "✅" for r in rows)
    pct = round(100 * done_tasks / total_tasks) if total_tasks else 0

    lines = [
        f"# {module.TITLE} — Specs",
        "",
        f"**Stack:** {module.STACK}",
        "",
        "Gerado por `tools/specs/gen.py` a partir de "
        f"`tools/specs/catalog_{module.APP}.py`. Não edite este arquivo à mão — "
        "marque os checkboxes em `tasks.md` / `acceptance.md` e rode o gerador de novo.",
        "",
        "⬜ Pendente · 🟨 Em andamento · ✅ Concluído · ⛔ Descartado",
        "",
        "## Resumo",
        "",
        "| | |",
        "| --- | --- |",
        f"| Features | {len(rows)} |",
        f"| Features concluídas | {done_features} |",
        f"| Tarefas concluídas | {done_tasks} / {total_tasks} ({pct}%) |",
        "",
    ]

    for epic_key, epic_name in module.EPICS.items():
        epic_rows = by_epic[epic_key]
        if not epic_rows:
            continue
        lines += [
            f"## {epic_name}",
            "",
            "| Status | Feature | Tarefas | Aceite |",
            "| :---: | --- | :---: | :---: |",
        ]
        for row in epic_rows:
            link = f"[{row['id']} — {row['title']}]({row['id']}/spec.md)"
            lines.append(
                f"| {row['symbol']} | {link} | {row['tasks'].done}/{row['tasks'].total} "
                f"| {row['acceptance'].done}/{row['acceptance'].total} |"
            )
        lines.append("")

    return "\n".join(lines)


def generate(module) -> None:
    docs_dir = ROOT / module.DOCS_DIR
    docs_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for feature in module.FEATURES:
        folder = docs_dir / feature["id"]
        folder.mkdir(exist_ok=True)

        acceptance_path = folder / "acceptance.md"
        tasks_path = folder / "tasks.md"

        checked_acceptance = read_checked(acceptance_path)
        checked_tasks = read_checked(tasks_path)

        (folder / "spec.md").write_text(render_spec(feature, module), encoding="utf-8")
        acceptance_path.write_text(
            render_acceptance(feature, checked_acceptance), encoding="utf-8"
        )
        tasks_path.write_text(render_tasks(feature, checked_tasks), encoding="utf-8")

        tasks_progress = count_checkboxes(tasks_path)
        acceptance_progress = count_checkboxes(acceptance_path)
        rows.append(
            {
                "id": feature["id"],
                "title": feature["title"],
                "epic": feature["epic"],
                "tasks": tasks_progress,
                "acceptance": acceptance_progress,
                "symbol": status_symbol(tasks_progress, acceptance_progress),
            }
        )

    (docs_dir / "README.md").write_text(render_index(module, rows), encoding="utf-8")

    done = sum(r["tasks"].done for r in rows)
    total = sum(r["tasks"].total for r in rows)
    print(f"{module.APP:9s} {len(rows):2d} features · {done}/{total} tarefas · {docs_dir}")


def main() -> int:
    for filename in CATALOGS:
        generate(load_catalog(filename))
    return 0


if __name__ == "__main__":
    sys.exit(main())
