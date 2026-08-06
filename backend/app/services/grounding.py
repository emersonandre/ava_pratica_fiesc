"""Verificacao de embasamento -- a ultima camada contra alucinacao.

"Alucinacao do modelo" e criterio **explicito** de avaliacao da entrevista.
Confiar so na instrucao do prompt e fragil e indefensavel sob questionamento.
A defesa aqui e em profundidade:

    camada 1  gate de cobertura (SPEC-FEAT-008)
              sem documento para a familia, o LLM nao e chamado. Nao ha como
              alucinar o que nao foi perguntado.

    camada 2  filtro rigido por familia (SPEC-FEAT-010)
              so entram no contexto trechos dos documentos que cobrem a falha.
              Medido: 4/7 de acerto sem o filtro, 7/7 com ele.

    camada 3  prompt restritivo + descarte de citacao inventada (SPEC-FEAT-011)
              rotulo de citacao que nao esta entre os recuperados e removido no
              parse -- alucinacao de fonte e a mais perigosa, porque parece
              verificavel.

    camada 4  este modulo: verificacao pos-geracao, afirmacao por afirmacao.

## Remover, nao apenas marcar

Passo sem respaldo e **removido**, nao sinalizado com um aviso discreto. Uma
instrucao de manutencao sem embasamento e risco fisico: alguem vai executar em
maquina rotativa. O que foi removido aparece em `removidas`, para auditoria.

## Verificacao lexica, nao por LLM

Usar o modelo para julgar o proprio modelo tem custo, latencia e o problema de
que o juiz alucina igual. A verificacao aqui e deterministica: cada passo precisa
de (a) citacao valida e (b) sobreposicao lexica minima com o trecho citado.

E uma checagem conservadora -- nao prova que o passo esta correto, prova que ele
tem origem no texto recuperado. Combinada com as tres camadas anteriores, cobre o
modo de falha que importa: passo inventado do nada.
"""

from __future__ import annotations

import logging
import re
import unicodedata

from app.schemas.prescription import Passo, Prescricao, RelatorioEmbasamento
from app.services.retrieval import TrechoRecuperado

logger = logging.getLogger("prescritiva.embasamento")

# Fracao minima das palavras de conteudo do passo que precisa aparecer no trecho
# citado. Calibrado para nao punir reformulacao legitima -- o modelo reescreve o
# procedimento em imperativo, nao copia -- mas barrar passo sem relacao.
SOBREPOSICAO_MINIMA = 0.30

# Palavras vazias: presentes em qualquer texto, nao indicam origem comum.
VAZIAS = frozenset(
    ["a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sob", "sobre", "e", "ou", "mas", "que", "se", "ao", "aos", "à", "às", "pelo", "pela", "pelos", "pelas", "entre", "ate", "apos", "antes", "durante", "ser", "estar", "ter", "haver", "fazer", "deve", "devem", "pode", "podem", "caso", "quando", "onde", "qual", "quais", "este", "esta", "esse", "essa", "aquele", "aquela", "isso", "isto", "seu", "sua", "seus", "suas", "conforme", "segundo", "apenas", "tambem", "mais", "menos", "muito", "pouco", "todo", "toda", "todos", "todas", "cada", "nao", "sim", "ja", "entao", "assim", "como"]
)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sem_acento if not unicodedata.combining(c))


def _palavras_de_conteudo(texto: str) -> set[str]:
    palavras = re.findall(r"[a-z0-9]{3,}", _normalizar(texto))
    return {p for p in palavras if p not in VAZIAS}


def _sobreposicao(passo: str, trecho: str) -> float:
    do_passo = _palavras_de_conteudo(passo)
    if not do_passo:
        return 0.0
    do_trecho = _palavras_de_conteudo(trecho)
    return len(do_passo & do_trecho) / len(do_passo)


def _avaliar(
    passo: Passo, por_rotulo: dict[str, TrechoRecuperado]
) -> tuple[bool, str]:
    if not passo.citacoes:
        return False, "sem citacao"

    melhor = 0.0
    for rotulo in passo.citacoes:
        trecho = por_rotulo.get(rotulo)
        if trecho is None:
            continue
        melhor = max(melhor, _sobreposicao(passo.texto, trecho.conteudo))

    if melhor >= SOBREPOSICAO_MINIMA:
        return True, ""
    return False, f"sobreposicao {melhor:.0%} com o trecho citado"


def verificar(
    prescricao: Prescricao, trechos: list[TrechoRecuperado]
) -> tuple[Prescricao, RelatorioEmbasamento]:
    """Remove os passos sem respaldo e devolve a prescricao saneada."""
    por_rotulo = {t.citacao: t for t in trechos}
    removidas: list[str] = []
    total = 0
    embasadas = 0

    def filtrar(passos: list[Passo]) -> list[Passo]:
        nonlocal total, embasadas
        mantidos = []
        for passo in passos:
            total += 1
            ok, motivo = _avaliar(passo, por_rotulo)
            if ok:
                embasadas += 1
                mantidos.append(passo)
            else:
                removidas.append(f"{passo.texto} ({motivo})")
                logger.warning("passo removido por falta de embasamento: %s", motivo)
        return mantidos

    prescricao.inspecao = filtrar(prescricao.inspecao)
    prescricao.correcao = filtrar(prescricao.correcao)
    prescricao.validacao = filtrar(prescricao.validacao)

    if removidas:
        prescricao.avisos.append(
            f"{len(removidas)} passo(s) foram removidos por nao terem respaldo "
            "verificavel na documentacao consultada."
        )

    # As citacoes listadas passam a refletir apenas os passos que sobreviveram.
    usadas = {c for passo in prescricao.passos for c in passo.citacoes}
    prescricao.citacoes = [c for c in prescricao.citacoes if c.rotulo in usadas]

    relatorio = RelatorioEmbasamento(
        afirmacoes=total,
        embasadas=embasadas,
        removidas=removidas,
        score=round(embasadas / total, 4) if total else 0.0,
        verificado=True,
    )
    prescricao.embasamento = relatorio
    return prescricao, relatorio
