"""SPEC-FEAT-013 e 014 -- criterios de aceite da API.

Usa a aplicacao completa, com banco real. Pulados sem banco.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.features import FEATURE_COLUMNS
from app.main import create_app
from app.models import SensorEvent
from app.settings import BACKEND_DIR
from tests.conftest import precisa_banco

pytestmark = precisa_banco

EVENTO_SEM_DOC = 163383  # eccentric_rotor: diagnosticado, mas sem documentacao

# JSON de exemplo da secao 2 do enunciado, exatamente como esta no PDF.
PAYLOAD_DO_ENUNCIADO = {
    "id": 114387,
    "created_at": "2026-06-01 21:32:53.911176+00:00",
    "z_rms_velocity_in_s": 0.0597,
    "z_rms_velocity_mm_s": 1.517,
    "temperature_f": 76.44,
    "temperature_c": 24.69,
    "x_rms_velocity_in_s": 0.0787,
    "x_rms_velocity_mm_s": 2.0,
    "z_peak_acceleration_g": 0.484,
    "x_peak_acceleration_g": 0.631,
    "z_peak_vel_comp_freq_hz": 61.0,
    "x_peak_vel_comp_freq_hz": 61.0,
    "z_rms_acceleration_g": 0.09,
    "x_rms_acceleration_g": 0.114,
    "z_kurtosis": 2.392,
    "x_kurtosis": 2.77,
    "z_crest_factor": 3.747,
    "x_crest_factor": 4.269,
    "z_peak_velocity_in_s": 0.0844,
    "z_peak_velocity_mm_s": 2.146,
    "x_peak_velocity_in_s": 0.1113,
    "x_peak_velocity_mm_s": 2.829,
    "z_high_freq_rms_accel_g": 0.129,
    "x_high_freq_rms_accel_g": 0.147,
    "fault": "cocked_rotor_2",
    "rpm": 1000.0,
}


def _variavel(nome: str) -> str:
    texto = (BACKEND_DIR / ".env").read_text(encoding="utf-8")
    achado = re.search(rf"(?m)^{nome}=(.+)$", texto)
    if not achado:
        pytest.skip(f"{nome} ausente em backend/.env")
    return achado.group(1).strip()


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app()) as cliente:
        yield cliente


@pytest.fixture(scope="module")
def token(client) -> str:
    resposta = client.post(
        "/api/v1/auth/token",
        json={
            "client_id": _variavel("API_CLIENT_ID"),
            "client_secret": _variavel("API_CLIENT_SECRET"),
        },
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["access_token"]


@pytest.fixture(scope="module")
def externo(token) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def interno() -> dict[str, str]:
    return {"X-Internal-Key": _variavel("INTERNAL_API_KEY")}


# --- Aceite: OpenAPI publicada e separada por superficie ---------------------
def test_openapi_lista_as_rotas_por_tag(client) -> None:
    caminhos = client.get("/openapi.json").json()["paths"]

    assert set(caminhos["/api/v1/predict"]["post"]["tags"]) == {"v1"}
    assert set(caminhos["/api/internal/stats/overview"]["get"]["tags"]) == {"internal"}
    assert {"/api/v1/predict", "/api/v1/upload_doc", "/api/v1/auth/token"} <= set(caminhos)


def test_documentacao_interativa_responde(client) -> None:
    assert client.get("/docs").status_code == 200


def test_raiz_redireciona_para_docs(client) -> None:
    resposta = client.get("/", follow_redirects=False)
    assert resposta.status_code == 307
    assert resposta.headers["location"] == "/docs"


# --- Aceite: payload do enunciado funciona sem adaptacao ---------------------
def test_json_do_enunciado_e_aceito(client, externo, base_populada) -> None:
    """Campos extras (`fault`, colunas imperiais) sao ignorados, nao rejeitados."""
    resposta = client.post("/api/v1/predict", headers=externo, json=PAYLOAD_DO_ENUNCIADO)
    assert resposta.status_code == 200, resposta.text


def test_resposta_e_consolidada(client, externo, base_populada) -> None:
    """Uma chamada traz diagnostico, evidencia, cobertura e prescricao ou recusa."""
    corpo = client.post(
        "/api/v1/predict", headers=externo, json=PAYLOAD_DO_ENUNCIADO
    ).json()

    assert {"diagnostico", "cobertura", "vizinhos", "tempos", "chamou_llm"} <= set(corpo)
    assert corpo["prescricao"] is not None or corpo["recusa"] is not None
    assert corpo["vizinhos"], "a evidencia deve vir junto, mesmo em recusa"


def test_tempos_por_etapa_presentes(client, externo, base_populada) -> None:
    tempos = client.post(
        "/api/v1/predict", headers=externo, json=PAYLOAD_DO_ENUNCIADO
    ).json()["tempos"]

    assert set(tempos) == {
        "similaridade_ms",
        "cobertura_ms",
        "recuperacao_ms",
        "geracao_ms",
        "verificacao_ms",
        "total_ms",
    }
    assert tempos["similaridade_ms"] > 0


# --- Aceite: campo faltante gera erro util -----------------------------------
def test_campo_obrigatorio_ausente_retorna_422(client, externo) -> None:
    incompleto = {k: v for k, v in PAYLOAD_DO_ENUNCIADO.items() if k != "z_kurtosis"}
    resposta = client.post("/api/v1/predict", headers=externo, json=incompleto)

    assert resposta.status_code == 422
    assert "z_kurtosis" in resposta.text


def test_pergunta_fora_de_dominio_e_recusada(client, externo, base_populada) -> None:
    resposta = client.post(
        "/api/v1/predict",
        headers=externo,
        json={**PAYLOAD_DO_ENUNCIADO, "pergunta": "Qual a capital da Franca?"},
    )
    assert resposta.status_code == 400
    assert "manutencao industrial" in resposta.json()["detail"]


# --- Aceite: gate impede prescricao sem documento ----------------------------
def test_familia_sem_documento_devolve_recusa(client, externo, session, base_populada) -> None:
    evento = session.get(SensorEvent, EVENTO_SEM_DOC)
    payload = {coluna: float(getattr(evento, coluna)) for coluna in FEATURE_COLUMNS}

    corpo = client.post("/api/v1/predict", headers=externo, json=payload).json()

    assert corpo["prescricao"] is None
    assert corpo["recusa"]["motivo"] == "sem_documento"
    assert corpo["chamou_llm"] is False
    assert "upload_doc" in corpo["recusa"]["sugestao"]
    # Recusar nao e devolver nada.
    assert corpo["evidencia"]["eventos_da_familia"] > 0


# --- Aceite: upload valida a entrada -----------------------------------------
def test_upload_rejeita_arquivo_que_nao_e_pdf(client, externo) -> None:
    resposta = client.post(
        "/api/v1/upload_doc",
        headers=externo,
        files={"file": ("falso.pdf", b"nao sou um pdf", "application/pdf")},
        data={"fault_family": "ventoinha"},
    )
    assert resposta.status_code == 400
    assert "PDF" in resposta.json()["detail"]


def test_upload_rejeita_familia_desconhecida(client, externo) -> None:
    pdf = (BACKEND_DIR.parent / "arquivos" / "Doc6.pdf").read_bytes()
    resposta = client.post(
        "/api/v1/upload_doc",
        headers=externo,
        files={"file": ("d.pdf", pdf, "application/pdf")},
        data={"fault_family": "familia_que_nao_existe"},
    )
    assert resposta.status_code == 422
    assert "familia_que_nao_existe" in resposta.json()["detail"]


def test_upload_rejeita_arquivo_vazio(client, externo) -> None:
    resposta = client.post(
        "/api/v1/upload_doc",
        headers=externo,
        files={"file": ("vazio.pdf", b"", "application/pdf")},
        data={"fault_family": "ventoinha"},
    )
    assert resposta.status_code == 400


def test_upload_do_mesmo_arquivo_nao_duplica(client, externo, base_populada) -> None:
    """Dedup por hash: reenviar Doc6 devolve o documento existente."""
    pdf = (BACKEND_DIR.parent / "arquivos" / "Doc6.pdf").read_bytes()
    resposta = client.post(
        "/api/v1/upload_doc",
        headers=externo,
        files={"file": ("Doc6.pdf", pdf, "application/pdf")},
        data={"fault_family": "cocked_rotor"},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["ja_existia"] is True
    assert corpo["cobertura_atualizada"] is False, "a familia ja era coberta"


# --- Aceite: superficie interna ----------------------------------------------
def test_overview_confere_com_o_banco(client, interno, base_populada) -> None:
    corpo = client.get("/api/internal/stats/overview", headers=interno).json()

    assert corpo["total_eventos"] == 166796
    assert corpo["eventos_holdout"] == 9061
    assert corpo["documentos_indexados"] == 6
    assert corpo["familias_cobertas"] + len(corpo["familias_descobertas"]) == corpo[
        "familias_problema"
    ]


def test_ranking_ordenado_por_ocorrencias(client, interno, base_populada) -> None:
    ranking = client.get("/api/internal/stats/overview", headers=interno).json()["ranking"]
    eventos = [item["eventos"] for item in ranking]

    assert eventos == sorted(eventos, reverse=True)
    assert ranking[0]["familia"] == "rolamento"


def test_faults_traz_status_de_cobertura(client, interno, base_populada) -> None:
    familias = {item["familia"]: item for item in client.get("/api/internal/faults", headers=interno).json()}

    assert familias["rolamento"]["coberta"] is True
    assert familias["rolamento"]["documentos"] == ["Doc1.pdf"]
    assert familias["ventoinha"]["coberta"] is False
    assert familias["normal"]["e_problema"] is False


def test_documentos_sinalizam_ocr(client, interno, base_populada) -> None:
    documentos = {d["arquivo"]: d for d in client.get("/api/internal/documents", headers=interno).json()}

    assert documentos["Doc1.pdf"]["metodo"] == "ocr"
    assert documentos["Doc1.pdf"]["confianca_ocr"] is not None
    assert documentos["Doc2.pdf"]["metodo"] == "text"


def test_timeline_responde(client, interno, base_populada) -> None:
    pontos = client.get(
        "/api/internal/stats/timeline?familia=rolamento", headers=interno
    ).json()
    assert pontos
    assert all(ponto["familia"] == "rolamento" for ponto in pontos)


def test_amostra_vem_sempre_do_holdout(client, interno, base_populada) -> None:
    for _ in range(5):
        evento = client.get("/api/internal/events/sample", headers=interno).json()
        assert evento["split"] == "holdout"


# --- Aceite: erro de negocio nao vaza stack trace ----------------------------
def test_erro_devolve_mensagem_e_nao_stack_trace(client, externo) -> None:
    resposta = client.post("/api/v1/predict", headers=externo, json={"rpm": 1000})
    assert resposta.status_code == 422
    assert "Traceback" not in resposta.text


# --- Aceite: observabilidade -------------------------------------------------
def test_toda_resposta_traz_identificador_de_requisicao(client) -> None:
    resposta = client.get("/api/health")
    assert resposta.headers.get("X-Request-ID")


def test_health_reporta_componentes(client) -> None:
    corpo = client.get("/api/health").json()
    nomes = {componente["nome"] for componente in corpo["componentes"]}
    assert {"banco", "eventos", "documentos", "scaler", "llm"} <= nomes


# --- Aceite: separacao entre as superficies ----------------------------------
def test_chave_interna_nao_abre_rota_externa(client, interno) -> None:
    resposta = client.post("/api/v1/predict", headers=interno, json=PAYLOAD_DO_ENUNCIADO)
    assert resposta.status_code == 401


def test_jwt_nao_abre_rota_interna(client, externo) -> None:
    assert client.get("/api/internal/faults", headers=externo).status_code == 401


def test_arquivos_do_enunciado_existem() -> None:
    """Guarda contra o repositorio ser clonado sem os dados de origem."""
    arquivos = BACKEND_DIR.parent / "arquivos"
    assert len(list(arquivos.glob("Doc*.pdf"))) == 6
    assert Path(BACKEND_DIR.parent / "dados" / "banner.csv").exists()
