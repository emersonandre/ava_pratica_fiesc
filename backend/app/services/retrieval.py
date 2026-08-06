"""Recuperacao de contexto para a prescricao.

Busca puramente semantica erra de um jeito especifico e perigoso neste dominio.
Os seis documentos compartilham quase o mesmo vocabulario -- "vibracao elevada",
"aquecimento nos mancais", "desgaste de rolamentos", "afrouxamento de parafusos".

Medicao com sete consultas-sonda, uma por assunto conhecido, **sem filtro**:

    acerto 4/7

    "ruido de impacto nas esferas do rolamento"  -> Doc4 (correias)
    "rotor desbalanceado, vibracao radial"       -> Doc6 (cocked rotor)
    "correia frouxa escorregando na polia"       -> Doc5 (polias)

A resposta sairia fluente, citada -- e apontando o procedimento errado. Em
manutencao industrial isso e pior que nao responder.

Por isso o filtro por familia e **rigido**, nao um reforco de score: a busca so
enxerga os documentos que cobrem a familia diagnosticada. Um peso alto ainda
deixaria passar documento errado; o corte duro elimina a classe inteira de erro.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.embeddings import embutir_consulta
from app.models import Document, DocumentChunk

Intencao = Literal["diagnostico", "correcao"]

# ~4 caracteres por token; orcamento folgado para caber com o prompt.
CARACTERES_POR_TOKEN = 4

# Secoes acionaveis, priorizadas quando o operador pede como corrigir.
SECAO_CORRECAO = re.compile(
    r"corre[cç][aã]o|procedimento|reparo|ajuste|substitui|manuten|valida",
    re.IGNORECASE,
)
SECAO_DIAGNOSTICO = re.compile(
    r"sintoma|diagn[oó]stico|caracteriza|causa|falha|vibra", re.IGNORECASE
)

PALAVRAS_DE_CORRECAO = re.compile(
    r"corrig|como faz|procedimento|reparar|consertar|resolver|ajustar|solucion",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class TrechoRecuperado:
    documento: str
    documento_id: int
    titulo: str
    metodo: str
    pagina_inicial: int
    pagina_final: int
    secao: str | None
    conteudo: str
    score: float

    @property
    def citacao(self) -> str:
        if self.pagina_inicial == self.pagina_final:
            return f"[{self.documento}, p. {self.pagina_inicial}]"
        return f"[{self.documento}, p. {self.pagina_inicial}-{self.pagina_final}]"


class SemCobertura(RuntimeError):
    """Recuperacao chamada para uma familia sem documento.

    Nao deveria acontecer: o gate (services/coverage) interrompe antes.
    """


def classificar_intencao(pergunta: str) -> Intencao:
    return "correcao" if PALAVRAS_DE_CORRECAO.search(pergunta) else "diagnostico"


def _prioridade(secao: str | None, intencao: Intencao) -> float:
    """Pequeno empurrao para a secao certa. Nao substitui o filtro por familia."""
    if not secao:
        return 0.0
    padrao = SECAO_CORRECAO if intencao == "correcao" else SECAO_DIAGNOSTICO
    return 0.05 if padrao.search(secao) else 0.0


def recuperar(
    session: Session,
    pergunta: str,
    *,
    ids_documentos: tuple[int, ...],
    orcamento_tokens: int = 1600,
    limite: int = 6,
) -> list[TrechoRecuperado]:
    """Busca semantica restrita aos documentos que cobrem a familia."""
    if not ids_documentos:
        raise SemCobertura(
            "recuperar() chamado sem documentos de cobertura -- o gate deveria "
            "ter interrompido o fluxo antes."
        )

    vetor = embutir_consulta(pergunta).tolist()
    distancia = DocumentChunk.embedding.cosine_distance(vetor).label("distancia")

    linhas = session.execute(
        select(
            Document.filename,
            Document.id,
            Document.title,
            Document.extraction_method,
            DocumentChunk.page_start,
            DocumentChunk.page_end,
            DocumentChunk.section,
            DocumentChunk.content,
            distancia,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        # Filtro RIGIDO: nenhum trecho fora da cobertura entra no contexto.
        .where(DocumentChunk.document_id.in_(ids_documentos))
        .order_by(distancia)
        .limit(limite)
    ).all()

    intencao = classificar_intencao(pergunta)
    trechos = [
        TrechoRecuperado(
            documento=linha.filename,
            documento_id=linha.id,
            titulo=linha.title,
            metodo=linha.extraction_method,
            pagina_inicial=linha.page_start,
            pagina_final=linha.page_end,
            secao=linha.section,
            conteudo=linha.content,
            score=round(1.0 - float(linha.distancia) + _prioridade(linha.section, intencao), 4),
        )
        for linha in linhas
    ]
    trechos.sort(key=lambda t: t.score, reverse=True)

    # Corta por orcamento sem truncar trecho: um procedimento pela metade e a
    # falha mais cara desta aplicacao.
    limite_caracteres = orcamento_tokens * CARACTERES_POR_TOKEN
    selecionados: list[TrechoRecuperado] = []
    usados = 0
    for trecho in trechos:
        if usados + len(trecho.conteudo) > limite_caracteres and selecionados:
            break
        selecionados.append(trecho)
        usados += len(trecho.conteudo)

    return selecionados
