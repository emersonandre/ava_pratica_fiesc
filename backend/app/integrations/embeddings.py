"""Embeddings locais.

`fastembed` roda o modelo em ONNX Runtime, na CPU. Escolha deliberada em vez de
`sentence-transformers`/PyTorch:

- dependencia de ~50 MB contra ~2,5 GB
- sem GPU, sem chamada de rede -- coerente com a restricao da secao 5 do enunciado,
  que exige operacao em estacao de trabalho
- custo zero por consulta, e a indexacao nao depende de credito de API

O modelo e multilingue porque documentos e perguntas dos operadores sao em
portugues.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np

from app.settings import get_settings

logger = logging.getLogger("prescritiva.embeddings")

# O e5 espera prefixos distintos para documento e consulta. Sem eles o modelo
# perde boa parte da qualidade de recuperacao.
PREFIXO_DOCUMENTO = "passage: "
PREFIXO_CONSULTA = "query: "


class DimensaoIncompativel(RuntimeError):
    """O modelo configurado gera vetores de tamanho diferente do indice."""


@lru_cache
def _modelo():
    from fastembed import TextEmbedding

    settings = get_settings()
    logger.info("carregando modelo de embedding %s", settings.embedding_model)
    return TextEmbedding(model_name=settings.embedding_model)


def _usa_prefixo_e5() -> bool:
    return "e5" in get_settings().embedding_model.lower()


def _validar(vetores: np.ndarray) -> np.ndarray:
    esperado = get_settings().embedding_dim
    if vetores.shape[1] != esperado:
        raise DimensaoIncompativel(
            f"O modelo gerou vetores de {vetores.shape[1]} dimensoes, mas o indice "
            f"espera {esperado}. Ajuste EMBEDDING_DIM e reindexe os documentos -- "
            "misturar dimensoes corromperia o indice em silencio."
        )
    return vetores


def embutir_documentos(textos: list[str]) -> np.ndarray:
    if not textos:
        return np.empty((0, get_settings().embedding_dim), dtype=np.float32)
    prefixo = PREFIXO_DOCUMENTO if _usa_prefixo_e5() else ""
    vetores = np.array(list(_modelo().embed([prefixo + t for t in textos])))
    return _validar(vetores)


def embutir_consulta(texto: str) -> np.ndarray:
    prefixo = PREFIXO_CONSULTA if _usa_prefixo_e5() else ""
    vetores = np.array(list(_modelo().embed([prefixo + texto])))
    return _validar(vetores)[0]
