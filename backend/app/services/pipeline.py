r"""Orquestracao da analise de um evento.

Une similaridade, gate de cobertura, recuperacao, geracao e verificacao na ordem
correta. E o ponto unico onde a sequencia esta escrita -- controllers apenas
chamam `analisar_evento`, entao nao ha caminho alternativo que pule o gate.

    similaridade -> gate -> [recusa]
                        \-> recuperacao -> geracao -> verificacao -> prescricao
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.features import load_scaler, to_vector
from app.integrations.llm import LLMIndisponivel
from app.schemas.prescription import Prescricao, Recusa
from app.schemas.similarity import SimilarityResult
from app.services import coverage, grounding, prescription, retrieval, similarity
from app.settings import get_settings

logger = logging.getLogger("prescritiva.pipeline")

PERGUNTA_PADRAO = "Como corrigir esta falha?"

# Perguntas fora do dominio de manutencao industrial sao recusadas antes de
# qualquer processamento. Barato, deterministico e cobre o caso mais obvio de
# uso indevido.
TERMOS_DE_DOMINIO = frozenset(
    ["falha", "defeito", "vibracao", "vibração", "rolamento", "mancal", "motor", "eixo", "acoplamento", "correia", "polia", "rotor", "desalinhamento", "desbalanceamento", "manutencao", "manutenção", "corrig", "corre", "inspec", "diagnost", "lubrific", "alinha", "balancea", "tensao", "tensão", "folga", "temperatura", "rpm", "rotacao", "rotação", "ruido", "ruído", "aquecimento", "desgaste", "parafuso", "torque", "equipamento", "maquina", "máquina"]
)


@dataclass(slots=True)
class Tempos:
    similaridade_ms: float = 0.0
    cobertura_ms: float = 0.0
    recuperacao_ms: float = 0.0
    geracao_ms: float = 0.0
    verificacao_ms: float = 0.0

    @property
    def total_ms(self) -> float:
        return round(
            self.similaridade_ms
            + self.cobertura_ms
            + self.recuperacao_ms
            + self.geracao_ms
            + self.verificacao_ms,
            1,
        )


@dataclass(slots=True)
class ResultadoAnalise:
    similaridade: SimilarityResult
    cobertura: coverage.Cobertura
    resposta: Prescricao | Recusa
    tempos: Tempos = field(default_factory=Tempos)
    trechos_usados: int = 0

    @property
    def chamou_llm(self) -> bool:
        return isinstance(self.resposta, Prescricao)


class _Cronometro:
    def __init__(self) -> None:
        self.inicio = time.perf_counter()

    def parar(self) -> float:
        return round((time.perf_counter() - self.inicio) * 1000, 1)


def pergunta_no_dominio(pergunta: str) -> bool:
    texto = pergunta.lower()
    return any(termo in texto for termo in TERMOS_DE_DOMINIO)


def analisar_evento(
    session: Session,
    payload: dict,
    *,
    pergunta: str = PERGUNTA_PADRAO,
    k: int | None = None,
    confianca_minima: float | None = None,
) -> ResultadoAnalise:
    """Fluxo completo, do JSON de sensor a prescricao ou recusa."""
    settings = get_settings()
    tempos = Tempos()

    # --- 1. similaridade -------------------------------------------------
    cronometro = _Cronometro()
    scaler = load_scaler(settings.artifacts_path)
    vetor = to_vector(scaler, payload)
    resultado = similarity.analisar(
        session, vetor.tolist(), k=k, confianca_minima=confianca_minima
    )
    tempos.similaridade_ms = cronometro.parar()

    # --- 2. gate de cobertura (ANTES do LLM) -----------------------------
    cronometro = _Cronometro()
    cobertura = coverage.verificar(
        session, resultado.familia_diagnosticada, e_problema=resultado.e_problema
    )
    tempos.cobertura_ms = cronometro.parar()

    if not cobertura.coberta:
        logger.info(
            "recusa motivo=%s familia=%s -- LLM nao chamado",
            cobertura.motivo,
            cobertura.familia,
        )
        return ResultadoAnalise(
            similaridade=resultado,
            cobertura=cobertura,
            resposta=Recusa(
                motivo=cobertura.motivo,
                mensagem=cobertura.mensagem,
                familia=cobertura.familia,
                sugestao=(
                    "Registre um documento para este defeito em POST /api/v1/upload_doc."
                    if cobertura.motivo == "sem_documento"
                    else None
                ),
            ),
            tempos=tempos,
        )

    # --- 3. recuperacao filtrada -----------------------------------------
    cronometro = _Cronometro()
    trechos = retrieval.recuperar(
        session, pergunta, ids_documentos=cobertura.ids_documentos
    )
    tempos.recuperacao_ms = cronometro.parar()

    if not trechos:
        return ResultadoAnalise(
            similaridade=resultado,
            cobertura=cobertura,
            resposta=Recusa(
                motivo="sem_documento",
                mensagem=(
                    "Ha documentacao vinculada a esta familia, mas nenhum trecho "
                    "relevante para a pergunta foi recuperado."
                ),
                familia=cobertura.familia,
            ),
            tempos=tempos,
        )

    # --- 4. geracao -------------------------------------------------------
    contexto = prescription.ContextoPrescricao(
        familia=cobertura.familia or "",
        confianca=resultado.confianca,
        eventos_similares=(
            resultado.evidencia.eventos_da_familia if resultado.evidencia else 0
        ),
        trechos=trechos,
        contexto_operacional=_descrever_contexto(resultado),
    )

    cronometro = _Cronometro()
    try:
        prescricao = prescription.gerar(contexto, pergunta)
    except (prescription.GeracaoInvalida, LLMIndisponivel) as erro:
        tempos.geracao_ms = cronometro.parar()
        logger.error("geracao falhou: %s", erro)
        return ResultadoAnalise(
            similaridade=resultado,
            cobertura=cobertura,
            resposta=Recusa(
                motivo="sem_diagnostico",
                mensagem=(
                    "O modelo de linguagem nao esta disponivel no momento. A analise "
                    "estatistica e os eventos similares continuam disponiveis."
                ),
                familia=cobertura.familia,
            ),
            tempos=tempos,
            trechos_usados=len(trechos),
        )
    tempos.geracao_ms = cronometro.parar()

    # --- 5. verificacao de embasamento ------------------------------------
    cronometro = _Cronometro()
    prescricao, relatorio = grounding.verificar(prescricao, trechos)
    tempos.verificacao_ms = cronometro.parar()

    logger.info(
        "prescricao familia=%s passos=%d embasamento=%.2f total=%.0fms",
        cobertura.familia,
        len(prescricao.passos),
        relatorio.score,
        tempos.total_ms,
    )

    # Se a verificacao removeu tudo, nao ha prescricao a entregar.
    if not prescricao.passos:
        return ResultadoAnalise(
            similaridade=resultado,
            cobertura=cobertura,
            resposta=Recusa(
                motivo="sem_documento",
                mensagem=(
                    "Nenhum passo gerado teve respaldo verificavel na documentacao. "
                    "O sistema prefere nao responder a entregar orientacao sem fonte."
                ),
                familia=cobertura.familia,
            ),
            tempos=tempos,
            trechos_usados=len(trechos),
        )

    return ResultadoAnalise(
        similaridade=resultado,
        cobertura=cobertura,
        resposta=prescricao,
        tempos=tempos,
        trechos_usados=len(trechos),
    )


def _descrever_contexto(resultado: SimilarityResult) -> str:
    if not resultado.evidencia or not resultado.evidencia.contexto_operacional:
        return ""
    ctx = resultado.evidencia.contexto_operacional
    return (
        f"Contexto operacional dos eventos semelhantes: RPM entre {ctx.rpm_min:.0f} "
        f"e {ctx.rpm_max:.0f}, temperatura entre {ctx.temp_min:.1f} e "
        f"{ctx.temp_max:.1f} C."
    )
