"""Divisao dos documentos em trechos indexaveis.

Os seis procedimentos seguem a mesma estrutura numerada: "1. Objetivo",
"3. Sintomas Comuns", "5. Procedimento de Correcao", "7. Validacao". Essas
fronteiras de secao sao fronteiras semanticas reais -- muito melhores que cortar a
cada N caracteres.

O corte por janela fixa quebraria um procedimento no meio, e um procedimento de
manutencao pela metade e a falha mais cara possivel nesta aplicacao: o tecnico
recebe metade dos passos de uma intervencao fisica em equipamento.

Cada trecho carrega documento, faixa de paginas e titulo da secao -- e o que
sustenta a citacao exibida ao operador.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.document_extraction import PaginaExtraida

# "1. Objetivo", "2.1 Desalinhamento Paralelo", "4.1 Acumulo de Material"
CABECALHO_SECAO = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2})*)\.?\s+([A-Za-zÀ-ÿ][^\n]{2,80})\s*$")

# Um trecho grande demais dilui o embedding; pequeno demais perde contexto.
MAX_CARACTERES = 1400
MIN_CARACTERES = 120
SOBREPOSICAO = 200


@dataclass(slots=True)
class Trecho:
    ordinal: int
    secao: str | None
    pagina_inicial: int
    pagina_final: int
    conteudo: str


@dataclass(slots=True)
class _Bloco:
    secao: str | None
    linhas: list[str]
    pagina_inicial: int
    pagina_final: int

    @property
    def texto(self) -> str:
        return "\n".join(self.linhas).strip()


def _dividir_em_secoes(paginas: list[PaginaExtraida]) -> list[_Bloco]:
    blocos: list[_Bloco] = []
    atual: _Bloco | None = None

    for pagina in paginas:
        for linha in pagina.texto.split("\n"):
            cabecalho = CABECALHO_SECAO.match(linha)
            if cabecalho:
                if atual and atual.texto:
                    blocos.append(atual)
                titulo = f"{cabecalho.group(1)}. {cabecalho.group(2).strip()}"
                atual = _Bloco(
                    secao=titulo,
                    linhas=[linha.strip()],
                    pagina_inicial=pagina.pagina,
                    pagina_final=pagina.pagina,
                )
                continue

            if atual is None:
                # Texto antes do primeiro cabecalho (capa, titulo do documento).
                atual = _Bloco(
                    secao=None,
                    linhas=[],
                    pagina_inicial=pagina.pagina,
                    pagina_final=pagina.pagina,
                )
            atual.linhas.append(linha)
            atual.pagina_final = pagina.pagina

    if atual and atual.texto:
        blocos.append(atual)
    return blocos


def _quebrar_por_tamanho(texto: str) -> list[str]:
    """Quebra uma secao longa em pedacos, sempre no fim de um paragrafo.

    A sobreposicao mantem o inicio do proximo pedaco ancorado no fim do anterior,
    para que um passo que atravesse a fronteira nao perca o contexto.
    """
    if len(texto) <= MAX_CARACTERES:
        return [texto]

    paragrafos = [p for p in texto.split("\n\n") if p.strip()]
    if len(paragrafos) == 1:
        paragrafos = [linha for linha in texto.split("\n") if linha.strip()]

    pedacos: list[str] = []
    atual: list[str] = []
    tamanho = 0

    for paragrafo in paragrafos:
        if tamanho + len(paragrafo) > MAX_CARACTERES and atual:
            pedacos.append("\n".join(atual))
            cauda = "\n".join(atual)[-SOBREPOSICAO:]
            atual = [cauda, paragrafo]
            tamanho = len(cauda) + len(paragrafo)
        else:
            atual.append(paragrafo)
            tamanho += len(paragrafo)

    if atual:
        pedacos.append("\n".join(atual))
    return pedacos


def dividir(paginas: list[PaginaExtraida]) -> list[Trecho]:
    trechos: list[Trecho] = []
    ordinal = 0

    for bloco in _dividir_em_secoes(paginas):
        texto = bloco.texto
        if len(texto) < MIN_CARACTERES:
            # Secao curta demais para virar trecho proprio: anexa a anterior para
            # nao gerar um embedding de "5. Validacao" sem conteudo nenhum.
            if trechos:
                trechos[-1].conteudo += "\n\n" + texto
                trechos[-1].pagina_final = bloco.pagina_final
                continue
            if not texto:
                continue

        for pedaco in _quebrar_por_tamanho(texto):
            # O titulo da secao entra no texto indexado: a consulta do operador
            # costuma usar as mesmas palavras do cabecalho.
            conteudo = (
                pedaco
                if bloco.secao and pedaco.startswith(bloco.secao)
                else (f"{bloco.secao}\n{pedaco}" if bloco.secao else pedaco)
            )
            trechos.append(
                Trecho(
                    ordinal=ordinal,
                    secao=bloco.secao,
                    pagina_inicial=bloco.pagina_inicial,
                    pagina_final=bloco.pagina_final,
                    conteudo=conteudo.strip(),
                )
            )
            ordinal += 1

    return trechos
