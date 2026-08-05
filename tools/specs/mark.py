"""Marca (ou desmarca) checkboxes de tasks.md / acceptance.md.

    python tools/specs/mark.py backend SPEC-FEAT-002 tasks --all
    python tools/specs/mark.py backend SPEC-FEAT-001 tasks "docker-compose" "config.py"
    python tools/specs/mark.py backend SPEC-FEAT-001 tasks --off "tasks.ps1"

Depois de marcar, roda o gerador para recalcular o indice de status.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINE_RE = re.compile(r"^(- \[)([ xX])(\] )(.*)$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", choices=["backend", "frontend"])
    parser.add_argument("feature", help="ex.: SPEC-FEAT-002")
    parser.add_argument("arquivo", choices=["tasks", "acceptance"])
    parser.add_argument("padroes", nargs="*", help="trechos do texto do item")
    parser.add_argument("--all", action="store_true", help="marca todos os itens")
    parser.add_argument("--off", action="store_true", help="desmarca em vez de marcar")
    args = parser.parse_args()

    path = ROOT / args.app / "docs" / args.feature / f"{args.arquivo}.md"
    if not path.exists():
        print(f"nao encontrado: {path}", file=sys.stderr)
        return 1

    marca = " " if args.off else "x"
    alterados: list[str] = []
    saida = []

    for linha in path.read_text(encoding="utf-8").splitlines():
        match = LINE_RE.match(linha)
        if match:
            texto = match.group(4)
            alvo = args.all or any(padrao.lower() in texto.lower() for padrao in args.padroes)
            if alvo:
                alterados.append(texto)
                linha = f"{match.group(1)}{marca}{match.group(3)}{texto}"
        saida.append(linha)

    path.write_text("\n".join(saida) + "\n", encoding="utf-8")

    verbo = "desmarcados" if args.off else "marcados"
    print(f"{args.app}/{args.feature}/{args.arquivo}.md: {len(alterados)} {verbo}")
    for texto in alterados:
        print(f"  - {texto[:90]}")

    subprocess.run([sys.executable, str(Path(__file__).parent / "gen.py")], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
