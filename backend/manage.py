#!/usr/bin/env python
"""Ponto de entrada administrativo do backend.

    python manage.py <comando> [opcoes]

Comandos:
    runserver     Sobe a API (uvicorn)
    initdb        Cria extensao, tabelas e indices (idempotente)
    ingest        Ingere o dados/banner.csv em sensor_events
    ingest-docs   Indexa os PDFs de arquivos/ no banco vetorial
    secrets       Gera segredos de autenticacao para colar no .env
    report        Gera os relatorios de analise em docs/analise/
    check         Verifica configuracao, banco e artefatos
    shell         REPL com sessao, modelos e settings ja carregados

FastAPI nao tem um `manage.py` embutido como o Django. Este arquivo cumpre o
mesmo papel: reunir as tarefas administrativas em um unico comando, para nao
espalhar `python -m ...` por README e documentacao.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Garante que `app` e `scripts` sejam importaveis independentemente de onde o
# comando foi chamado.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def cmd_runserver(args: argparse.Namespace) -> int:
    import uvicorn

    from app.settings import get_settings

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=args.host or settings.api_host,
        port=args.port or settings.api_port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )
    return 0


def cmd_initdb(args: argparse.Namespace) -> int:
    from scripts.init_db import run

    return run(drop=args.drop)


def cmd_ingest(args: argparse.Namespace) -> int:
    from scripts.ingest_csv import run

    return run(limit=args.limit)


def cmd_ingest_docs(args: argparse.Namespace) -> int:
    from scripts.ingest_docs import run

    return run(forcar=args.force)


def cmd_secrets(_: argparse.Namespace) -> int:
    from scripts.gen_secrets import run

    return run()


def cmd_report(args: argparse.Namespace) -> int:
    from scripts.report_documents import run as run_documentos
    from scripts.report_hallucination import run as run_alucinacao
    from scripts.report_similarity import run as run_similaridade
    from scripts.report_taxonomy import run as run_taxonomy

    relatorios = {
        "taxonomia": run_taxonomy,
        "similaridade": run_similaridade,
        "documentos": run_documentos,
        "alucinacao": run_alucinacao,
    }
    alvos = relatorios if args.nome == "all" else {args.nome: relatorios[args.nome]}
    for nome, funcao in alvos.items():
        print(f"-- {nome}")
        codigo = funcao()
        if codigo != 0:
            return codigo
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    from sqlalchemy import func, select

    from app.core.features import FEATURE_DIM, scaler_path
    from app.database import ping, session_scope
    from app.models import SensorEvent
    from app.settings import get_settings

    settings = get_settings()
    ok = True

    banco = ping()
    print(f"{'ok ' if banco else 'FALHA'} banco         {settings.database_url.split('@')[-1]}")
    ok &= banco

    if banco:
        with session_scope() as session:
            total = session.scalar(select(func.count()).select_from(SensorEvent)) or 0
        print(f"{'ok ' if total else 'FALHA'} eventos       {total:,}".replace(",", "."))
        ok &= bool(total)

    scaler = scaler_path(settings.artifacts_path)
    print(f"{'ok ' if scaler.exists() else 'FALHA'} scaler        {scaler.name} ({FEATURE_DIM}d)")
    ok &= scaler.exists()

    llm = bool(settings.llm_api_key)
    print(f"{'ok ' if llm else '-- '} llm           {settings.llm_provider}/{settings.llm_model}")

    try:
        settings.require_auth()
        print("ok  autenticacao  segredos configurados")
    except RuntimeError as erro:
        print(f"--  autenticacao  {erro}")

    return 0 if ok else 1


def cmd_shell(_: argparse.Namespace) -> int:
    import code

    from app import models
    from app.database import session_scope
    from app.settings import get_settings

    with session_scope() as session:
        contexto = {
            "session": session,
            "settings": get_settings(),
            **{nome: getattr(models, nome) for nome in models.__all__},
        }
        banner = "Disponivel: session, settings, " + ", ".join(models.__all__)
        code.interact(banner=banner, local=contexto, exitmsg="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("runserver", help="sobe a API")
    p.add_argument("--host", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--reload", action="store_true", help="recarrega ao salvar (dev)")
    p.set_defaults(func=cmd_runserver)

    p = sub.add_parser("initdb", help="cria extensao, tabelas e indices")
    p.add_argument("--drop", action="store_true", help="derruba as tabelas antes de recriar")
    p.set_defaults(func=cmd_initdb)

    p = sub.add_parser("ingest", help="ingere o banner.csv")
    p.add_argument("--limit", type=int, default=None, help="ingere apenas N linhas")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("ingest-docs", help="indexa os PDFs de arquivos/")
    p.add_argument("--force", action="store_true", help="reindexa mesmo se ja existir")
    p.set_defaults(func=cmd_ingest_docs)

    p = sub.add_parser("secrets", help="gera segredos de autenticacao")
    p.set_defaults(func=cmd_secrets)

    p = sub.add_parser("report", help="gera relatorios de analise")
    p.add_argument(
        "nome", nargs="?", default="all", choices=["all", "taxonomia", "similaridade", "documentos", "alucinacao"]
    )
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("check", help="verifica configuracao, banco e artefatos")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("shell", help="REPL com sessao e modelos carregados")
    p.set_defaults(func=cmd_shell)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
