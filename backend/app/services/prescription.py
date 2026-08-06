"""Geracao da resposta prescritiva.

A saida precisa ser **prescritiva**, nao descritiva: o tecnico quer saber o que
fazer, em que ordem, e como confirmar que resolveu.

## Divisao de trabalho entre codigo e modelo

    numeros (quantos eventos, desde quando, frequencia)  -> banco    (SPEC-FEAT-005)
    qual documento consultar                             -> codigo   (SPEC-FEAT-008)
    quais trechos entram no contexto                     -> codigo   (SPEC-FEAT-010)
    redacao dos passos a partir desses trechos           -> modelo
    verificacao de que cada passo tem respaldo           -> codigo   (SPEC-FEAT-012)

O modelo so redige. Nao escolhe fonte, nao inventa numero e nao decide se pode
responder. Essa fronteira e o que sustenta a defesa contra alucinacao.

## Citacao por passo, nao por resposta

Uma citacao no rodape nao prova que *aquele* passo veio do manual. Cada item de
inspecao, correcao e validacao carrega suas proprias citacoes, e a
SPEC-FEAT-012 confere uma a uma.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from app.integrations.llm import (
    LLMIndisponivel,
    Mensagem,
    OrcamentoEstourado,
    get_provider,
)
from app.schemas.prescription import Citacao, Passo, Prescricao
from app.services.retrieval import TrechoRecuperado

logger = logging.getLogger("prescritiva.geracao")

MAX_TENTATIVAS = 2

PROMPT_SISTEMA = """Voce e um assistente tecnico de manutencao industrial. Redige
procedimentos de correcao para tecnicos de chao de fabrica, em portugues do Brasil.

REGRAS ABSOLUTAS:

1. Use EXCLUSIVAMENTE as informacoes dos trechos de documentacao fornecidos.
   Nao complete com conhecimento proprio, mesmo que voce saiba a resposta.
2. Todo passo que voce escrever deve citar o trecho que o sustenta, usando o
   rotulo exato fornecido (ex.: [Doc2.pdf, p. 4]).
3. Se a documentacao nao cobrir algum aspecto, diga isso em `avisos`. Nao preencha
   a lacuna.
4. Nao invente numeros, tolerancias, torques, prazos ou especificacoes que nao
   estejam escritos nos trechos.
5. Escreva passos acionaveis, no imperativo, um por item. Nada de paragrafos.
6. Use a terminologia dos manuais (mancal, acoplamento, crest factor, folga).

Responda SOMENTE com um objeto JSON valido nesta forma:

{
  "diagnostico": "uma frase explicando a falha identificada",
  "inspecao":  [{"texto": "...", "citacoes": ["[Doc2.pdf, p. 3]"]}],
  "correcao":  [{"texto": "...", "citacoes": ["[Doc2.pdf, p. 5]"]}],
  "validacao": [{"texto": "...", "citacoes": ["[Doc2.pdf, p. 6]"]}],
  "avisos": ["pontos que exigem julgamento humano ou que a documentacao nao cobre"]
}
"""

PROMPT_USUARIO = """## Evento analisado

Familia de falha identificada: {familia}
Confianca do diagnostico por similaridade: {confianca:.0%}
Eventos semelhantes no historico: {eventos}

{contexto_operacional}

## Pergunta do operador

{pergunta}

## Trechos da documentacao tecnica

{trechos}

---
Redija a resposta em JSON conforme as regras. Cada passo deve citar ao menos um
dos rotulos acima. Nao use nenhum outro rotulo.
"""


class GeracaoInvalida(RuntimeError):
    """O modelo nao produziu uma resposta no formato exigido."""


@dataclass(slots=True)
class ContextoPrescricao:
    familia: str
    confianca: float
    eventos_similares: int
    trechos: list[TrechoRecuperado]
    contexto_operacional: str = ""


def _formatar_trechos(trechos: list[TrechoRecuperado]) -> str:
    partes = []
    for trecho in trechos:
        cabecalho = f"### {trecho.citacao}"
        if trecho.secao:
            cabecalho += f" — {trecho.secao}"
        if trecho.metodo == "ocr":
            cabecalho += "  (texto obtido por OCR)"
        partes.append(f"{cabecalho}\n{trecho.conteudo}")
    return "\n\n".join(partes)


def _citacoes_disponiveis(trechos: list[TrechoRecuperado]) -> dict[str, Citacao]:
    return {
        trecho.citacao: Citacao(
            documento=trecho.documento,
            pagina_inicial=trecho.pagina_inicial,
            pagina_final=trecho.pagina_final,
            secao=trecho.secao,
            metodo=trecho.metodo,
        )
        for trecho in trechos
    }


def _extrair_json(texto: str) -> dict:
    """Tolera cerca de bloco de codigo, que alguns modelos insistem em produzir."""
    limpo = re.sub(r"^```(?:json)?|```$", "", texto.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(limpo)
    except json.JSONDecodeError as erro:
        inicio, fim = limpo.find("{"), limpo.rfind("}")
        if inicio == -1 or fim <= inicio:
            raise GeracaoInvalida(f"resposta nao e JSON: {texto[:200]!r}") from erro
        try:
            return json.loads(limpo[inicio : fim + 1])
        except json.JSONDecodeError as erro2:
            raise GeracaoInvalida(f"JSON malformado: {texto[:200]!r}") from erro2


def _montar_passos(itens: list, validos: set[str]) -> list[Passo]:
    """Converte a saida do modelo em passos, descartando citacao inventada.

    Uma citacao que nao esta entre as recuperadas e alucinacao de fonte -- o tipo
    mais perigoso, porque parece verificavel. E removida aqui; se o passo ficar
    sem nenhuma citacao, a SPEC-FEAT-012 o elimina.
    """
    passos: list[Passo] = []
    for item in itens or []:
        if isinstance(item, str):
            passos.append(Passo(texto=item, citacoes=[]))
            continue
        if not isinstance(item, dict) or not item.get("texto"):
            continue
        citacoes = [c for c in item.get("citacoes", []) if c in validos]
        inventadas = [c for c in item.get("citacoes", []) if c not in validos]
        if inventadas:
            logger.warning("citacoes inexistentes descartadas: %s", inventadas)
        passos.append(Passo(texto=str(item["texto"]).strip(), citacoes=citacoes))
    return passos


def gerar(contexto: ContextoPrescricao, pergunta: str) -> Prescricao:
    """Gera a prescricao. Assume que o gate de cobertura ja autorizou."""
    if not contexto.trechos:
        raise GeracaoInvalida(
            "gerar() chamado sem trechos recuperados -- o gate deveria ter "
            "interrompido o fluxo antes de chegar ao modelo."
        )

    disponiveis = _citacoes_disponiveis(contexto.trechos)
    mensagens = [
        Mensagem("system", PROMPT_SISTEMA),
        Mensagem(
            "user",
            PROMPT_USUARIO.format(
                familia=contexto.familia,
                confianca=contexto.confianca,
                eventos=contexto.eventos_similares,
                contexto_operacional=contexto.contexto_operacional,
                pergunta=pergunta,
                trechos=_formatar_trechos(contexto.trechos),
            ),
        ),
    ]

    provider = get_provider()
    ultimo_erro: Exception | None = None

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = provider.completar(mensagens, formato_json=True)
            dados = _extrair_json(resposta.texto)
        except GeracaoInvalida as erro:
            ultimo_erro = erro
            logger.warning("tentativa %d produziu formato invalido: %s", tentativa, erro)
            continue
        except OrcamentoEstourado as erro:
            # Nao adianta repetir com o mesmo orcamento: falharia igual.
            raise GeracaoInvalida(str(erro)) from erro
        except LLMIndisponivel:
            raise

        validos = set(disponiveis)
        prescricao = Prescricao(
            diagnostico=str(dados.get("diagnostico", "")).strip(),
            inspecao=_montar_passos(dados.get("inspecao"), validos),
            correcao=_montar_passos(dados.get("correcao"), validos),
            validacao=_montar_passos(dados.get("validacao"), validos),
            avisos=[str(a) for a in dados.get("avisos", []) if str(a).strip()],
        )

        usadas = {c for passo in prescricao.passos for c in passo.citacoes}
        prescricao.citacoes = [disponiveis[rotulo] for rotulo in sorted(usadas)]

        if any(t.metodo == "ocr" for t in contexto.trechos):
            prescricao.avisos.append(
                "Parte da documentacao consultada foi obtida por OCR de paginas em "
                "imagem. Confirme os valores criticos no documento original."
            )

        if not prescricao.passos:
            ultimo_erro = GeracaoInvalida("o modelo nao produziu nenhum passo")
            logger.warning("tentativa %d nao produziu passos", tentativa)
            continue

        return prescricao

    raise GeracaoInvalida(
        f"o modelo nao produziu resposta valida em {MAX_TENTATIVAS} tentativas: "
        f"{ultimo_erro}"
    )
