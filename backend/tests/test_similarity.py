"""SPEC-FEAT-005 -- criterios de aceite do motor de similaridade.

Testes de integracao: exigem banco populado. Sao pulados se ele nao estiver
disponivel, para que a suite continue rodando em maquina limpa.
"""

from __future__ import annotations

import numpy as np
import pytest
from sqlalchemy import select

from app.core.features import FEATURE_DIM, load_scaler, to_vector
from app.models import SensorEvent
from app.repositories import sensor_event as repo
from app.services import similarity
from app.settings import get_settings
from tests.conftest import precisa_banco

pytestmark = precisa_banco


@pytest.fixture(scope="module")
def scaler():
    return load_scaler(get_settings().artifacts_path)


def _vetor_de(evento: SensorEvent) -> list[float]:
    return [float(v) for v in evento.features]


# --- Aceite: sem vazamento na busca ------------------------------------------
def test_nenhum_vizinho_vem_do_holdout(session, base_populada) -> None:
    evento = repo.amostra_holdout(session)
    vizinhos = repo.buscar_vizinhos(session, _vetor_de(evento), k=50)

    ids = [v.id for v in vizinhos]
    splits = session.scalars(select(SensorEvent.split).where(SensorEvent.id.in_(ids))).all()
    assert set(splits) == {"train"}


# --- Aceite: busca filtrada retorna resultado (regressao do pos-filtro) ------
def test_busca_a_partir_do_holdout_nao_volta_vazia(session, base_populada) -> None:
    """Regressao: com indice HNSW nao-parcial, o pos-filtro zerava o resultado."""
    for _ in range(5):
        evento = repo.amostra_holdout(session)
        assert repo.buscar_vizinhos(session, _vetor_de(evento), k=50)


def test_retorna_exatamente_k_vizinhos(session, base_populada) -> None:
    """Regressao: `hnsw.ef_search` padrao (40) truncava k=50 em silencio."""
    evento = repo.amostra_holdout(session)
    for k in (10, 50, 100):
        assert len(repo.buscar_vizinhos(session, _vetor_de(evento), k=k)) == k


# --- Aceite: a busca recupera o vizinho correto -------------------------------
def test_evento_do_historico_se_encontra_como_vizinho_mais_proximo(session, base_populada) -> None:
    """Consultar com um vetor identico a um registro do historico deve devolve-lo
    em primeiro lugar, com similaridade ~1. E o teste de sanidade da busca.

    Nota: mesmo nesse caso a confianca da vizinhanca costuma ficar baixa. As
    familias se sobrepoem fortemente no espaco de features -- os 50 vizinhos de um
    evento de `rolamento` frequentemente incluem varias outras familias. Nao e um
    defeito da busca, e a caracteristica do dataset medida em
    docs/analise/similaridade.md.
    """
    evento = session.scalars(
        select(SensorEvent)
        .where(SensorEvent.split == "train", SensorEvent.fault_family == "rolamento")
        .limit(1)
    ).one()

    vizinhos = repo.buscar_vizinhos(session, _vetor_de(evento), k=50)
    assert vizinhos[0].id == evento.id
    assert vizinhos[0].similarity == pytest.approx(1.0, abs=1e-4)


def test_familias_se_sobrepoem_no_espaco_de_features(session, base_populada) -> None:
    """Documenta a limitacao medida: a vizinhanca raramente e homogenea.

    Se este teste passar a falhar porque a confianca ficou alta, o motor melhorou
    e os limiares de docs/analise/similaridade.md precisam ser recalibrados.
    """
    evento = session.scalars(
        select(SensorEvent)
        .where(SensorEvent.split == "train", SensorEvent.fault_family == "rolamento")
        .limit(1)
    ).one()

    resultado = similarity.analisar(session, _vetor_de(evento), k=50)
    familias = {v.fault_family for v in resultado.vizinhos}
    assert len(familias) > 1, "vizinhanca homogenea -- recalibre os limiares"


def test_confianca_e_a_fracao_do_voto_vencedor(session, base_populada) -> None:
    evento = repo.amostra_holdout(session)
    resultado = similarity.analisar(session, _vetor_de(evento), k=50)

    assert resultado.votos == sorted(resultado.votos, key=lambda v: v.peso, reverse=True)
    assert resultado.confianca == pytest.approx(resultado.votos[0].peso, abs=1e-4)
    assert sum(v.peso for v in resultado.votos) == pytest.approx(1.0, abs=1e-6)


# --- Aceite: abstencao quando a vizinhanca esta dividida ---------------------
def test_limiar_alto_forca_abstencao(session, base_populada) -> None:
    evento = repo.amostra_holdout(session)
    resultado = similarity.analisar(session, _vetor_de(evento), k=50, confianca_minima=1.01)

    assert resultado.familia_diagnosticada is None
    assert resultado.motivo == "vizinhanca_dividida"
    assert resultado.aviso
    # Mesmo se abstendo, entrega os eventos similares para analise humana.
    assert resultado.vizinhos


def test_estado_operacional_nao_vira_prescricao(session, base_populada) -> None:
    evento = session.scalars(
        select(SensorEvent)
        .where(SensorEvent.split == "train", SensorEvent.fault_family == "motor_desligado")
        .limit(1)
    ).one()

    resultado = similarity.analisar(session, _vetor_de(evento), k=50)
    assert resultado.e_problema is False
    if resultado.familia_diagnosticada:
        assert resultado.motivo == "estado_operacional"


# --- Aceite: familia sem historico nunca e diagnosticada ---------------------
def test_falta_fase_nao_existe_no_historico(session, base_populada) -> None:
    """800 registros de `falta_fase`, todos no holdout. Nenhum no treino."""
    familias = repo.familias_com_historico(session)
    assert "falta_fase" not in familias


def test_nenhum_vizinho_pode_ser_de_familia_sem_historico(session, base_populada) -> None:
    evento = repo.amostra_holdout(session, familia="falta_fase")
    resultado = similarity.analisar(session, _vetor_de(evento), k=50)
    assert all(v.fault_family != "falta_fase" for v in resultado.vizinhos)


# --- Aceite: evidencia confere com o banco -----------------------------------
def test_evidencia_bate_com_consulta_direta(session, base_populada) -> None:
    evento = repo.amostra_holdout(session)
    resultado = similarity.analisar(session, _vetor_de(evento), k=50)

    familia = resultado.familia_diagnosticada or resultado.votos[0].fault_family
    estatisticas = repo.estatisticas_familia(session, familia)

    assert resultado.evidencia.eventos_da_familia == estatisticas.total
    assert resultado.evidencia.vizinhos_da_familia == sum(
        1 for v in resultado.vizinhos if v.fault_family == familia
    )
    assert sum(p.total for p in resultado.evidencia.linha_do_tempo) == estatisticas.total


def test_vetor_de_inferencia_tem_a_dimensao_do_banco(session, base_populada, scaler) -> None:
    evento = repo.amostra_holdout(session)
    payload = {
        coluna: float(getattr(evento, coluna))
        for coluna in __import__("app.core.features", fromlist=["x"]).FEATURE_COLUMNS
    }
    vetor = to_vector(scaler, payload)

    assert len(vetor) == FEATURE_DIM
    # O vetor recalculado bate com o gravado na ingestao.
    np.testing.assert_allclose(vetor, np.array(_vetor_de(evento)), atol=1e-4)
