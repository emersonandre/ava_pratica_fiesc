"""Camada de acesso ao modelo de linguagem.

OpenAI e DeepSeek falam o mesmo protocolo, entao uma implementacao cobre os dois:
muda `base_url` e `model` no `.env`. E o mesmo ponto por onde um servidor local
compativel com OpenAI (modelo quantizado nos 16 GB de VRAM da secao 5 do
enunciado) entra sem tocar em regra de negocio.

A camada tambem e onde ficam as garantias operacionais: timeout, retry com
backoff, teto de tokens e log de consumo. Nenhum servico chama o SDK direto.
"""

from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Literal

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.settings import Settings, get_settings

logger = logging.getLogger("prescritiva.llm")

Papel = Literal["system", "user", "assistant"]

# Endpoint de cada provider. O `base_url` e resolvido pelo NOME do provider, nao
# por qual caminho (texto ou visao) esta sendo usado -- confundir os dois faz o
# cliente de visao enviar uma chave DeepSeek para a OpenAI e receber 401.
BASE_URLS: dict[str, str | None] = {
    "openai": None,  # padrao do SDK
    "deepseek": "https://api.deepseek.com",
}


class LLMIndisponivel(RuntimeError):
    """Falha de comunicacao com o provider, ja esgotadas as tentativas."""


class CapacidadeAusente(RuntimeError):
    """O modelo configurado nao suporta o recurso pedido (ex.: visao)."""


@dataclass(frozen=True, slots=True)
class Mensagem:
    papel: Papel
    conteudo: str


@dataclass(slots=True)
class RespostaLLM:
    texto: str
    modelo: str
    tokens_entrada: int
    tokens_saida: int
    latencia_s: float
    bruto: dict[str, Any] = field(default_factory=dict)


class LLMProvider:
    """Cliente unico para providers compativeis com o protocolo da OpenAI."""

    def __init__(self, settings: Settings, *, para_visao: bool = False) -> None:
        self._settings = settings
        self.para_visao = para_visao

        if para_visao:
            self.nome = settings.vision_provider
            self.modelo = settings.vision_model
            chave = settings.vision_api_key or settings.llm_api_key
        else:
            self.nome = settings.llm_provider
            self.modelo = settings.llm_model
            chave = settings.llm_api_key

        if not chave:
            raise LLMIndisponivel(
                "Credencial do provider ausente. Preencha LLM_API_KEY em backend/.env."
            )

        # `LLM_BASE_URL` explicito vence; senao usa o endpoint do provider.
        if para_visao:
            self.base_url = BASE_URLS.get(self.nome)
        else:
            self.base_url = settings.llm_base_url or BASE_URLS.get(self.nome)

        self._cliente = OpenAI(
            api_key=chave,
            base_url=self.base_url,
            timeout=settings.llm_timeout_seconds,
        )

    # -- chamadas ---------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(
            (APIConnectionError, APITimeoutError, RateLimitError)
        ),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _chamar(self, mensagens: list[dict[str, Any]], **opcoes: Any) -> Any:
        return self._cliente.chat.completions.create(
            model=self.modelo, messages=mensagens, **opcoes
        )

    def _executar(self, mensagens: list[dict[str, Any]], **opcoes: Any) -> RespostaLLM:
        inicio = time.perf_counter()
        try:
            resposta = self._chamar(mensagens, **opcoes)
        except (APIConnectionError, APITimeoutError, RateLimitError) as erro:
            raise LLMIndisponivel(
                f"Provider {self.nome} indisponivel apos as tentativas: {erro}"
            ) from erro
        except APIStatusError as erro:
            raise LLMIndisponivel(
                f"Provider {self.nome} recusou a requisicao ({erro.status_code}): "
                f"{getattr(erro, 'message', erro)}"
            ) from erro

        latencia = time.perf_counter() - inicio
        uso = resposta.usage
        entrada = getattr(uso, "prompt_tokens", 0) or 0
        saida = getattr(uso, "completion_tokens", 0) or 0

        logger.info(
            "llm modelo=%s tokens_entrada=%d tokens_saida=%d latencia=%.2fs",
            self.modelo,
            entrada,
            saida,
            latencia,
        )

        return RespostaLLM(
            texto=resposta.choices[0].message.content or "",
            modelo=self.modelo,
            tokens_entrada=entrada,
            tokens_saida=saida,
            latencia_s=round(latencia, 3),
        )

    def completar(
        self,
        mensagens: list[Mensagem],
        *,
        max_tokens: int | None = None,
        temperatura: float | None = None,
        formato_json: bool = False,
    ) -> RespostaLLM:
        opcoes: dict[str, Any] = {
            "max_tokens": max_tokens or self._settings.llm_max_tokens,
            "temperature": (
                temperatura
                if temperatura is not None
                else self._settings.llm_temperature
            ),
        }
        if formato_json:
            opcoes["response_format"] = {"type": "json_object"}

        payload = [{"role": m.papel, "content": m.conteudo} for m in mensagens]
        return self._executar(payload, **opcoes)

    def transcrever_imagem(
        self, imagem_png: bytes, prompt: str, *, max_tokens: int = 4000
    ) -> RespostaLLM:
        """Transcreve o texto de uma imagem. Usado apenas no OCR offline.

        Nao ha lista fixa de modelos com visao: ela envelhece mal. A capacidade e
        descoberta na primeira chamada -- se o provider recusar a imagem, o erro
        vira `CapacidadeAusente` com a orientacao de trocar `VISION_MODEL`.
        """
        base64_png = base64.b64encode(imagem_png).decode("ascii")
        mensagens = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_png}"},
                    },
                ],
            }
        ]
        try:
            # Temperatura zero: transcricao nao e tarefa criativa.
            return self._executar(mensagens, max_tokens=max_tokens, temperature=0.0)
        except LLMIndisponivel as erro:
            if _parece_recusa_de_imagem(str(erro)):
                raise CapacidadeAusente(
                    f"O modelo {self.modelo!r} do provider {self.nome!r} nao aceita "
                    "imagem. O OCR precisa de um modelo com visao -- ajuste "
                    "VISION_PROVIDER/VISION_MODEL em backend/.env."
                ) from erro
            raise


def _parece_recusa_de_imagem(mensagem: str) -> bool:
    texto = mensagem.lower()
    pistas = ("image", "vision", "multimodal", "image_url", "content type")
    return any(pista in texto for pista in pistas)


@lru_cache
def get_provider() -> LLMProvider:
    return LLMProvider(get_settings())


@lru_cache
def get_vision_provider() -> LLMProvider:
    return LLMProvider(get_settings(), para_visao=True)
