"""Ingestao do banner.csv em sensor_events.

    python -m app.scripts.ingest_csv

Etapas: le o CSV -> normaliza a taxonomia (SPEC-FEAT-002) -> define o split
temporal -> ajusta e persiste o scaler (SPEC-FEAT-003) -> grava com upsert por id.

Sobre o split: o dataset tem um corte temporal natural. Todo rotulo com prefixo
`new_` foi coletado entre 10 e 16/jun/2026 e todo o restante e de ate 09/jun.
Isso vira o holdout sem precisar sortear nada. Sorteio aleatorio seria um erro
grave aqui: amostras da mesma sessao de ensaio foram coletadas com segundos de
diferenca, entao cairiam dos dois lados e o vizinho mais proximo de um registro
de teste seria praticamente ele mesmo -- acuracia inflada e falsa.

A regra e verificada contra as datas reais, nao assumida pelo nome.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.config import get_settings
from app.core import features as feat
from app.core.taxonomy import UnknownFaultLabel, normalize_fault
from app.db import get_engine, session_scope
from app.models import SensorEvent

# Fronteira do holdout, confirmada na exploracao dos dados.
HOLDOUT_START = datetime(2026, 6, 10, tzinfo=timezone.utc)

# Colunas metricas persistidas alem do vetor (para exibicao e analise).
STORED_COLUMNS = feat.FEATURE_COLUMNS

# O protocolo do PostgreSQL aceita no maximo 65535 parametros por comando.
# 7 colunas de identificacao/rotulo + as metricas + o vetor.
COLUMNS_PER_ROW = 7 + len(STORED_COLUMNS) + 1
BATCH_SIZE = 60_000 // COLUMNS_PER_ROW


def carregar_csv(path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["created_at"])
    if df["created_at"].dt.tz is None:
        df["created_at"] = df["created_at"].dt.tz_localize("UTC")
    return df


def aplicar_taxonomia(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza cada rotulo distinto uma vez so e propaga por merge."""
    rotulos = df["fault"].unique()
    linhas = []
    for rotulo in rotulos:
        try:
            resultado = normalize_fault(rotulo)
        except UnknownFaultLabel as erro:
            ids = df.loc[df["fault"] == rotulo, "id"].head(3).tolist()
            raise SystemExit(
                f"Ingestao abortada. {erro} Exemplos de id afetados: {ids}"
            ) from erro
        linhas.append(
            {
                "fault": rotulo,
                "canonical_fault": resultado.canonical,
                "fault_family": resultado.family,
                "is_problem": resultado.is_problem,
            }
        )
    return df.merge(pd.DataFrame(linhas), on="fault", how="left")


def definir_split(df: pd.DataFrame) -> pd.DataFrame:
    """Marca train/holdout e valida que nome e data contam a mesma historia."""
    por_nome = df["fault"].str.startswith("new_")
    por_data = df["created_at"] >= HOLDOUT_START

    divergentes = int((por_nome != por_data).sum())
    if divergentes:
        exemplos = df.loc[por_nome != por_data, ["id", "fault", "created_at"]].head(5)
        raise SystemExit(
            f"Prefixo `new_` e data do holdout divergem em {divergentes} registros. "
            f"A regra de split precisa ser revista antes de prosseguir.\n{exemplos}"
        )

    df["split"] = pd.Series("train", index=df.index).mask(por_nome, "holdout")
    return df


def ajustar_scaler(df: pd.DataFrame):
    """Ajusta o scaler so no treino e sem `motor_desligado`.

    Motor parado (RPM = 0) e estado valido e continua no banco, mas nao representa
    operacao: incluir esses registros deslocaria a media de RPM e comprimiria a
    escala das demais features.
    """
    treino = df[df["split"] == "train"]
    excluir = treino["fault_family"] == "motor_desligado"
    scaler = feat.fit_scaler(treino, exclude_mask=excluir)
    print(
        f"scaler         ajustado em {len(treino) - int(excluir.sum()):,} registros "
        f"(exclui {int(excluir.sum())} de motor_desligado)".replace(",", ".")
    )
    return scaler


def gravar(df: pd.DataFrame, vetores) -> int:
    colunas = [
        "id",
        "created_at",
        "raw_fault",
        "canonical_fault",
        "fault_family",
        "is_problem",
        "split",
        *STORED_COLUMNS,
    ]
    registros = df.rename(columns={"fault": "raw_fault"}).loc[:, colunas]
    payload = registros.to_dict(orient="records")
    for linha, vetor in zip(payload, vetores, strict=True):
        linha["features"] = vetor.tolist()

    total = 0
    with session_scope() as session:
        for inicio in range(0, len(payload), BATCH_SIZE):
            lote = payload[inicio : inicio + BATCH_SIZE]
            stmt = insert(SensorEvent).values(lote)
            # Upsert por id: reexecutar a ingestao nao duplica nem falha.
            stmt = stmt.on_conflict_do_update(
                index_elements=[SensorEvent.id],
                set_={
                    coluna: stmt.excluded[coluna]
                    for coluna in [*colunas[1:], "features"]
                },
            )
            session.execute(stmt)
            total += len(lote)
            print(f"  gravados {total:,}/{len(payload):,}".replace(",", "."), end="\r")
    print()
    return total


def resumo() -> None:
    with session_scope() as session:
        total = session.scalar(select(func.count()).select_from(SensorEvent))
        por_split = session.execute(
            select(
                SensorEvent.split,
                func.count(),
                func.min(SensorEvent.created_at),
                func.max(SensorEvent.created_at),
            ).group_by(SensorEvent.split)
        ).all()

    print(f"\ntotal          {total:,}".replace(",", "."))
    for split, quantidade, inicio, fim in sorted(por_split):
        print(
            f"  {split:8s} {quantidade:>7,}".replace(",", ".")
            + f"  {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="ingere apenas N linhas")
    args = parser.parse_args()

    settings = get_settings()
    print(f"origem         {settings.csv_path}")

    df = carregar_csv(settings.csv_path)
    if args.limit:
        df = df.head(args.limit)
    print(f"linhas         {len(df):,}".replace(",", "."))

    df = aplicar_taxonomia(df)
    print(
        f"taxonomia      {df['fault'].nunique()} rotulos brutos -> "
        f"{df['fault_family'].nunique()} familias"
    )

    df = definir_split(df)
    scaler = ajustar_scaler(df)
    caminho = feat.save_scaler(scaler, settings.artifacts_path)
    print(f"scaler salvo   {caminho.name} ({feat.FEATURE_DIM} dimensoes)")

    vetores = feat.transform(scaler, df)
    gravar(df, vetores)

    # ANALYZE mantem o planejador ciente do volume recem-inserido.
    with get_engine().begin() as connection:
        connection.exec_driver_sql("ANALYZE sensor_events")

    resumo()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
