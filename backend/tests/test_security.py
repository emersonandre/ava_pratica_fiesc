"""SPEC-FEAT-016 -- criterios de aceite da autenticacao.

Nao dependem de banco: exercitam a camada de seguranca isoladamente, com
`Settings` construido no teste. Rodam em maquina limpa.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.security import (
    create_access_token,
    require_internal_key,
    require_scope,
)
from app.settings import Settings, get_settings

CLIENT_ID = "cliente-teste"
CLIENT_SECRET = "segredo-de-cliente-para-teste-1234567890"
JWT_SECRET = "segredo-jwt-para-teste-0987654321-abcdefgh"
INTERNAL_KEY = "chave-interna-para-teste-abcdefghijklmno"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret=JWT_SECRET,
        api_client_id=CLIENT_ID,
        api_client_secret=CLIENT_SECRET,
        internal_api_key=INTERNAL_KEY,
        llm_api_key="fake",
        jwt_expire_minutes=60,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """App minimo com uma rota por escopo e uma interna.

    Exercita as dependencias de seguranca sem arrastar banco nem LLM para o teste.
    """
    from app.controllers.v1 import auth

    app = FastAPI()
    app.include_router(auth.router)

    # Dependencia que so protege a rota vai no decorador, nao na assinatura:
    # declarada como parametro, o FastAPI tenta interpreta-la como campo da
    # requisicao e responde 422 em vez de 401.
    @app.post("/protegido/predict", dependencies=[Depends(require_scope("predict"))])
    def _predict() -> dict:
        return {"ok": True}

    @app.post("/protegido/upload", dependencies=[Depends(require_scope("upload"))])
    def _upload() -> dict:
        return {"ok": True}

    @app.get("/protegido/interno", dependencies=[Depends(require_internal_key)])
    def _interno() -> dict:
        return {"ok": True}

    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def _token(client: TestClient, *, scopes: list[str] | None = None) -> str:
    corpo: dict = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    if scopes is not None:
        corpo["scopes"] = scopes
    resposta = client.post("/api/v1/auth/token", json=corpo)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["access_token"]


# --- Aceite: endpoint externo sem token e recusado ---------------------------
def test_sem_cabecalho_authorization(client: TestClient) -> None:
    resposta = client.post("/protegido/predict")
    assert resposta.status_code == 401
    assert "Authorization" in resposta.json()["detail"]


def test_esquema_diferente_de_bearer(client: TestClient) -> None:
    resposta = client.post("/protegido/predict", headers={"Authorization": "Basic YWJjOjEyMw=="})
    assert resposta.status_code == 401


# --- Aceite: token valido e aceito -------------------------------------------
def test_token_valido_da_acesso(client: TestClient) -> None:
    token = _token(client)
    resposta = client.post("/protegido/predict", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == 200


def test_resposta_do_token_traz_expiracao_e_escopos(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/auth/token",
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
    )
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["expires_in"] == 3600
    assert set(corpo["scopes"]) == {"predict", "upload", "ingest"}


# --- Aceite: credencial errada nao emite token -------------------------------
@pytest.mark.parametrize(
    ("client_id", "client_secret"),
    [
        (CLIENT_ID, "errado"),
        ("errado", CLIENT_SECRET),
        ("errado", "errado"),
        ("", ""),
    ],
)
def test_credencial_invalida(client: TestClient, client_id: str, client_secret: str) -> None:
    resposta = client.post(
        "/api/v1/auth/token",
        json={"client_id": client_id, "client_secret": client_secret},
    )
    assert resposta.status_code == 401
    assert "access_token" not in resposta.json()


def test_erro_nao_distingue_id_de_segredo(client: TestClient) -> None:
    """Mensagens diferentes revelariam quais client_id existem."""
    a = client.post("/api/v1/auth/token", json={"client_id": CLIENT_ID, "client_secret": "x"})
    b = client.post("/api/v1/auth/token", json={"client_id": "x", "client_secret": CLIENT_SECRET})
    assert a.json()["detail"] == b.json()["detail"]


# --- Aceite: escopo e verificado ---------------------------------------------
def test_token_sem_escopo_de_upload_nao_envia_documento(client: TestClient) -> None:
    """Um integrador somente-leitura nao injeta documento na base de conhecimento."""
    token = _token(client, scopes=["predict"])
    cabecalho = {"Authorization": f"Bearer {token}"}

    assert client.post("/protegido/predict", headers=cabecalho).status_code == 200

    negado = client.post("/protegido/upload", headers=cabecalho)
    assert negado.status_code == 403
    assert "upload" in negado.json()["detail"]


def test_nao_e_possivel_pedir_escopo_alem_do_concedido(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/auth/token",
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scopes": ["predict", "administrador"],
        },
    )
    assert resposta.status_code == 400
    assert "administrador" in resposta.json()["detail"]


# --- Aceite: token expirado e rejeitado --------------------------------------
def test_token_expirado(client: TestClient, settings: Settings) -> None:
    expirado = jwt.encode(
        {
            "sub": CLIENT_ID,
            "scopes": ["predict"],
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "iss": "manutencao-prescritiva",
        },
        JWT_SECRET,
        algorithm="HS256",
    )
    resposta = client.post("/protegido/predict", headers={"Authorization": f"Bearer {expirado}"})
    assert resposta.status_code == 401
    assert "expirado" in resposta.json()["detail"].lower()


def test_mensagem_de_expirado_difere_da_de_invalido(client: TestClient) -> None:
    invalido = client.post("/protegido/predict", headers={"Authorization": "Bearer nao-e-um-jwt"})
    assert invalido.status_code == 401
    assert "invalido" in invalido.json()["detail"].lower()


# --- Aceite: assinatura adulterada e rejeitada -------------------------------
def test_token_assinado_com_outro_segredo(client: TestClient) -> None:
    forjado = jwt.encode(
        {
            "sub": CLIENT_ID,
            "scopes": ["predict", "upload"],
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iss": "manutencao-prescritiva",
        },
        "outro-segredo-completamente-diferente",
        algorithm="HS256",
    )
    resposta = client.post("/protegido/predict", headers={"Authorization": f"Bearer {forjado}"})
    assert resposta.status_code == 401


def test_token_de_outro_emissor(client: TestClient) -> None:
    de_terceiro = jwt.encode(
        {
            "sub": CLIENT_ID,
            "scopes": ["predict"],
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iss": "outro-sistema",
        },
        JWT_SECRET,
        algorithm="HS256",
    )
    resposta = client.post("/protegido/predict", headers={"Authorization": f"Bearer {de_terceiro}"})
    assert resposta.status_code == 401


# --- Aceite: endpoint interno exige a chave ----------------------------------
def test_interno_sem_chave(client: TestClient) -> None:
    assert client.get("/protegido/interno").status_code == 401


def test_interno_com_chave_errada(client: TestClient) -> None:
    resposta = client.get("/protegido/interno", headers={"X-Internal-Key": "chave-errada"})
    assert resposta.status_code == 401


def test_interno_com_chave_correta(client: TestClient) -> None:
    resposta = client.get("/protegido/interno", headers={"X-Internal-Key": INTERNAL_KEY})
    assert resposta.status_code == 200


def test_jwt_nao_serve_para_endpoint_interno(client: TestClient) -> None:
    """As duas superficies sao independentes: um mecanismo nao substitui o outro."""
    token = _token(client)
    resposta = client.get("/protegido/interno", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == 401


# --- Aceite: segredos nao vazam ----------------------------------------------
def test_nenhum_segredo_aparece_nas_respostas_de_erro(client: TestClient) -> None:
    respostas = [
        client.post("/api/v1/auth/token", json={"client_id": "x", "client_secret": "y"}),
        client.post("/protegido/predict"),
        client.get("/protegido/interno", headers={"X-Internal-Key": "errada"}),
    ]
    for resposta in respostas:
        corpo = resposta.text
        assert JWT_SECRET not in corpo
        assert CLIENT_SECRET not in corpo
        assert INTERNAL_KEY not in corpo


def test_payload_do_token_nao_carrega_segredo(client: TestClient) -> None:
    """O JWT e assinado, nao criptografado: qualquer um le o payload."""
    token = _token(client)
    payload = jwt.decode(token, options={"verify_signature": False})
    assert JWT_SECRET not in str(payload)
    assert CLIENT_SECRET not in str(payload)
    assert set(payload) >= {"sub", "scopes", "exp", "iat", "iss"}


# --- Aceite: API nao sobe sem segredo ----------------------------------------
def test_require_auth_nomeia_as_variaveis_ausentes() -> None:
    incompleto = Settings(
        jwt_secret="", api_client_id="", api_client_secret="", internal_api_key=""
    )
    with pytest.raises(RuntimeError) as erro:
        incompleto.require_auth()

    mensagem = str(erro.value)
    for variavel in (
        "JWT_SECRET",
        "API_CLIENT_ID",
        "API_CLIENT_SECRET",
        "INTERNAL_API_KEY",
    ):
        assert variavel in mensagem


def test_require_auth_passa_com_tudo_configurado(settings: Settings) -> None:
    settings.require_auth()


def test_token_carrega_expiracao_curta(settings: Settings) -> None:
    resposta = create_access_token(settings, "cliente", ["predict"])
    payload = jwt.decode(
        resposta.access_token, JWT_SECRET, algorithms=["HS256"], issuer="manutencao-prescritiva"
    )
    vida = datetime.fromtimestamp(payload["exp"], UTC) - datetime.now(UTC)
    assert timedelta(minutes=0) < vida <= timedelta(minutes=settings.jwt_expire_minutes)
