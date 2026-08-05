"""Configuracao central da aplicacao.

Toda configuracao vem de variaveis de ambiente (`backend/.env`). Nada de valor
sensivel no codigo. A validacao acontece na criacao das `Settings`, entao um
`.env` incompleto quebra na inicializacao com o nome da variavel faltante --
nao no meio de uma requisicao.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/settings/config.py -> settings -> app -> backend -> raiz do repositorio
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Banco de dados ---
    database_url: str = Field(
        default="postgresql+psycopg://prescritiva:prescritiva@localhost:5433/prescritiva"
    )

    # --- LLM ---
    llm_provider: Literal["openai", "deepseek"] = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    llm_base_url: str = ""
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    llm_timeout_seconds: int = 60

    # --- Visao (OCR offline) ---
    vision_provider: Literal["openai", "deepseek"] = "openai"
    vision_api_key: str = ""
    vision_model: str = "gpt-4.1-mini"

    # --- Embeddings ---
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_dim: int = 384

    # --- Similaridade ---
    similarity_k: int = 50
    ood_distance_threshold: float = 0.35

    # --- API ---
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    log_level: str = "INFO"

    # --- Autenticacao externa (JWT) ---
    # Usada por /api/v1/predict e /api/v1/upload_doc, consumidos por sistemas
    # da planta. Token emitido em /api/v1/auth/token contra credencial de cliente.
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    api_client_id: str = ""
    api_client_secret: str = ""

    # --- Autenticacao interna (frontend) ---
    # Chave estatica trocada entre o proxy do frontend e a API, dentro da rede.
    # Nunca chega ao navegador.
    internal_api_key: str = ""

    # --- Caminhos (relativos a raiz do repositorio) ---
    data_csv: str = "dados/banner.csv"
    docs_dir: str = "arquivos"
    artifacts_dir: str = "backend/artifacts"

    @field_validator("llm_base_url")
    @classmethod
    def _default_base_url(cls, value: str, info) -> str:
        """DeepSeek exige base_url; OpenAI usa o default do SDK."""
        if value:
            return value
        if info.data.get("llm_provider") == "deepseek":
            return "https://api.deepseek.com"
        return ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def csv_path(self) -> Path:
        return PROJECT_ROOT / self.data_csv

    @property
    def documents_path(self) -> Path:
        return PROJECT_ROOT / self.docs_dir

    @property
    def artifacts_path(self) -> Path:
        path = PROJECT_ROOT / self.artifacts_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    def require_llm(self) -> None:
        """Falha cedo e com clareza quando a credencial do LLM nao esta configurada."""
        if not self.llm_api_key:
            raise RuntimeError(
                "LLM_API_KEY nao configurada. Copie backend/.env.example para "
                "backend/.env e preencha a chave do provider escolhido."
            )

    def require_auth(self) -> None:
        """Falha na inicializacao se a API subir sem segredo configurado.

        Uma API industrial exposta sem autenticacao e pior que uma API fora do ar:
        o problema so aparece depois. Melhor nao subir.
        """
        faltando = [
            nome
            for nome, valor in (
                ("JWT_SECRET", self.jwt_secret),
                ("API_CLIENT_ID", self.api_client_id),
                ("API_CLIENT_SECRET", self.api_client_secret),
                ("INTERNAL_API_KEY", self.internal_api_key),
            )
            if not valor
        ]
        if faltando:
            raise RuntimeError(
                f"Variaveis de autenticacao ausentes: {', '.join(faltando)}. "
                "Gere-as com `python manage.py secrets` e preencha backend/.env."
            )

    def require_vision(self) -> None:
        if not (self.vision_api_key or self.llm_api_key):
            raise RuntimeError(
                "VISION_API_KEY (ou LLM_API_KEY) nao configurada. O OCR dos documentos "
                "depende de um modelo com suporte a imagem."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
