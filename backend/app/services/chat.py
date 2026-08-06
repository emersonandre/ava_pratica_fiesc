"""Chat prescritivo com historico.

Perguntas de acompanhamento passam pelas mesmas quatro camadas antialucinacao da
prescricao inicial. O historico entra no prompt, mas nao substitui a recuperacao:
cada pergunta busca trechos de novo, sempre restrita aos documentos que cobrem a
familia diagnosticada.

Isso importa: sem recuperar de novo, o modelo responderia a segunda pergunta com
o que "lembra" do contexto anterior -- que e exatamente onde ele inventa.
"""

from __future__ import annotations

import logging
import re
import time

from sqlalchemy.orm import Session

from app.core.features import load_scaler, to_vector
from app.integrations.llm import LLMIndisponivel, Mensagem, OrcamentoEstourado, get_provider
from app.schemas.chat import ChatResponse, MensagemChat
from app.schemas.predict import TemposOut
from app.schemas.prescription import Citacao, Passo, Prescricao
from app.services import coverage, grounding, retrieval, similarity
from app.services.retrieval import TrechoRecuperado
from app.settings import get_settings

logger = logging.getLogger("prescritiva.chat")

MAX_HISTORICO = 6

PROMPT_SISTEMA = """Voce e um assistente tecnico de manutencao industrial, falando com
um tecnico de chao de fabrica em portugues do Brasil.

REGRAS ABSOLUTAS:

1. Use EXCLUSIVAMENTE os trechos de documentacao fornecidos nesta mensagem.
   Nao complete com conhecimento proprio, mesmo que voce saiba a resposta.
2. Cite a fonte de cada afirmacao tecnica usando o rotulo exato fornecido
   (ex.: [Doc2.pdf, p. 4]). Cite no meio do texto, logo apos a afirmacao.
3. Se os trechos nao responderem a pergunta, diga isso com todas as letras.
   Nao preencha a lacuna.
4. Nao invente numeros, tolerancias, torques ou prazos que nao estejam escritos.
5. Seja direto. O tecnico esta na frente da maquina, nao lendo um manual.
   Responda em ate 6 frases, salvo se pedirem uma lista de passos.

Responda em texto corrido ou lista, sem JSON."""

PROMPT_PERGUNTA = """## Contexto do evento

Falha identificada: {familia}
Confianca do diagnostico: {confianca:.0%}

## Conversa ate agora

{historico}

## Pergunta atual

{pergunta}

## Trechos da documentacao tecnica

{trechos}

---
Responda a pergunta atual usando somente os trechos acima, citando os rotulos."""

# Perguntas propostas depois da primeira resposta. Aceleram a demonstracao e
# mostram o que o sistema consegue responder.
SUGESTOES = [
    "Quais ferramentas preciso para isso?",
    "Como confirmo que o problema foi resolvido?",
    "Quais os sintomas dessa falha?",
    "O que causa esse tipo de defeito?",
    "Que cuidados de seguranca devo tomar?",
]


def _formatar_historico(mensagens: list[MensagemChat]) -> str:
    if not mensagens:
        return "(primeira pergunta)"
    recentes = mensagens[-MAX_HISTORICO:]
    return "\n".join(
        f"{'Tecnico' if m.papel == 'operador' else 'Assistente'}: {m.texto}"
        for m in recentes
    )


def _formatar_trechos(trechos: list[TrechoRecuperado]) -> str:
    partes = []
    for trecho in trechos:
        cabecalho = f"### {trecho.citacao}"
        if trecho.secao:
            cabecalho += f" — {trecho.secao}"
        if trecho.metodo == "ocr":
            cabecalho += "  (obtido por OCR)"
        partes.append(f"{cabecalho}\n{trecho.conteudo}")
    return "\n\n".join(partes)


def _citacoes_no_texto(texto: str, trechos: list[TrechoRecuperado]) -> list[Citacao]:
    """Extrai do texto as citacoes que existem de verdade entre os trechos."""
    disponiveis = {t.citacao: t for t in trechos}
    encontradas = re.findall(r"\[[^\]]+\]", texto)
    usadas: dict[str, Citacao] = {}

    for rotulo in encontradas:
        trecho = disponiveis.get(rotulo)
        if trecho is None:
            continue
        usadas[rotulo] = Citacao(
            documento=trecho.documento,
            pagina_inicial=trecho.pagina_inicial,
            pagina_final=trecho.pagina_final,
            secao=trecho.secao,
            metodo=trecho.metodo,
            trecho=trecho.conteudo,
        )
    return list(usadas.values())


def _limpar_citacoes_inventadas(
    texto: str, trechos: list[TrechoRecuperado]
) -> tuple[str, int]:
    """Remove rotulos de citacao que nao correspondem a nenhum trecho recuperado.

    Alucinacao de fonte e a mais perigosa: parece verificavel. Melhor a frase
    ficar sem citacao -- e ser derrubada na verificacao -- do que exibir uma
    referencia falsa.
    """
    validos = {t.citacao for t in trechos}
    removidas = 0

    def substituir(ocorrencia: re.Match[str]) -> str:
        nonlocal removidas
        if ocorrencia.group(0) in validos:
            return ocorrencia.group(0)
        removidas += 1
        return ""

    return re.sub(r"\[[^\]]+\]", substituir, texto), removidas


def conversar(session: Session, requisicao) -> ChatResponse:
    """Responde uma pergunta ancorada em um evento de sensor."""
    settings = get_settings()
    inicio = time.perf_counter()
    tempos = TemposOut(
        similaridade_ms=0,
        cobertura_ms=0,
        recuperacao_ms=0,
        geracao_ms=0,
        verificacao_ms=0,
        total_ms=0,
    )

    # --- diagnostico e gate: iguais aos da prescricao ---------------------
    marca = time.perf_counter()
    scaler = load_scaler(settings.artifacts_path)
    vetor = to_vector(scaler, requisicao.evento.to_feature_dict())
    resultado = similarity.analisar(
        session, vetor.tolist(), confianca_minima=requisicao.confianca_minima
    )
    tempos.similaridade_ms = round((time.perf_counter() - marca) * 1000, 1)

    marca = time.perf_counter()
    cobertura = coverage.verificar(
        session, resultado.familia_diagnosticada, e_problema=resultado.e_problema
    )
    tempos.cobertura_ms = round((time.perf_counter() - marca) * 1000, 1)

    if not cobertura.coberta:
        tempos.total_ms = round((time.perf_counter() - inicio) * 1000, 1)
        logger.info("chat recusou motivo=%s -- LLM nao chamado", cobertura.motivo)
        return ChatResponse(
            resposta=cobertura.mensagem,
            familia=cobertura.familia,
            cobertura=cobertura.motivo,
            recusou=True,
            tempos=tempos,
        )

    # --- recuperacao por pergunta, sempre ---------------------------------
    marca = time.perf_counter()
    trechos = retrieval.recuperar(
        session, requisicao.pergunta, ids_documentos=cobertura.ids_documentos
    )
    tempos.recuperacao_ms = round((time.perf_counter() - marca) * 1000, 1)

    if not trechos:
        tempos.total_ms = round((time.perf_counter() - inicio) * 1000, 1)
        return ChatResponse(
            resposta=(
                "Nao encontrei nada na documentacao desta falha que responda a essa "
                "pergunta. Reformule ou consulte o procedimento completo."
            ),
            familia=cobertura.familia,
            cobertura=cobertura.motivo,
            recusou=True,
            tempos=tempos,
        )

    # --- geracao -----------------------------------------------------------
    mensagens = [
        Mensagem("system", PROMPT_SISTEMA),
        Mensagem(
            "user",
            PROMPT_PERGUNTA.format(
                familia=cobertura.familia,
                confianca=resultado.confianca,
                historico=_formatar_historico(requisicao.mensagens),
                pergunta=requisicao.pergunta,
                trechos=_formatar_trechos(trechos),
            ),
        ),
    ]

    marca = time.perf_counter()
    try:
        resposta_llm = get_provider().completar(mensagens)
    except (LLMIndisponivel, OrcamentoEstourado) as erro:
        tempos.geracao_ms = round((time.perf_counter() - marca) * 1000, 1)
        tempos.total_ms = round((time.perf_counter() - inicio) * 1000, 1)
        logger.error("chat falhou na geracao: %s", erro)
        return ChatResponse(
            resposta=(
                "O modelo de linguagem nao respondeu. A analise estatistica e os "
                "eventos similares continuam disponiveis."
            ),
            familia=cobertura.familia,
            cobertura=cobertura.motivo,
            recusou=True,
            tempos=tempos,
        )
    tempos.geracao_ms = round((time.perf_counter() - marca) * 1000, 1)

    texto, inventadas = _limpar_citacoes_inventadas(resposta_llm.texto.strip(), trechos)
    if inventadas:
        logger.warning("%d citacoes inexistentes removidas da resposta", inventadas)

    # --- verificacao de embasamento ----------------------------------------
    marca = time.perf_counter()
    citacoes = _citacoes_no_texto(texto, trechos)
    embasamento = _verificar(texto, citacoes, trechos)
    tempos.verificacao_ms = round((time.perf_counter() - marca) * 1000, 1)
    tempos.total_ms = round((time.perf_counter() - inicio) * 1000, 1)

    return ChatResponse(
        resposta=texto,
        citacoes=citacoes,
        embasamento=embasamento,
        familia=cobertura.familia,
        cobertura=cobertura.motivo,
        recusou=False,
        sugestoes=SUGESTOES[:3],
        tempos=tempos,
    )


def _verificar(texto: str, citacoes: list[Citacao], trechos: list[TrechoRecuperado]):
    """Aplica a verificacao de embasamento frase a frase.

    Reaproveita o mesmo mecanismo da prescricao: cada frase com pretensao tecnica
    precisa ter sobreposicao lexica com algum trecho recuperado.
    """
    frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto) if len(f.strip()) > 40]
    if not frases:
        return None

    passos = [Passo(texto=f, citacoes=[c.rotulo for c in citacoes]) for f in frases]
    _, relatorio = grounding.verificar(
        Prescricao(diagnostico="", correcao=passos), trechos
    )
    return relatorio
