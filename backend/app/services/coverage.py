"""Gate de cobertura documental.

Regra literal da secao 3 do enunciado:

    "O sistema deve se deter unicamente a problemas que possuem documentos, caso
    contrario deve reportar que ainda nao existe o problema identificado e sugerir
    ao usuario para registrar um novo documento para o defeito."

Isso e regra de negocio, e regra de negocio nao se implementa como pedido educado
no prompt. O gate roda **antes** de qualquer chamada ao modelo: sem documento, o
LLM sequer e chamado -- nao ha como alucinar o que nao foi perguntado.

Quatro desfechos, com mensagens distintas. Colapsar todos em "nao sei"
desperdicaria a informacao mais util da solucao:

    coberto                 ha documento para a familia; segue para o RAG
    sem_documento           familia identificada, mas nenhum documento a cobre
    estado_operacional      o padrao e um estado (normal, motor parado), nao falha
    sem_diagnostico         a vizinhanca nao sustenta um diagnostico
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.taxonomy import FAMILY_DESCRIPTIONS, PROBLEM_FAMILIES
from app.models import Document, FaultCoverage

Motivo = Literal["coberto", "sem_documento", "estado_operacional", "sem_diagnostico"]


@dataclass(frozen=True, slots=True)
class DocumentoRef:
    id: int
    titulo: str
    arquivo: str
    metodo: str
    paginas: int


@dataclass(frozen=True, slots=True)
class Cobertura:
    familia: str | None
    coberta: bool
    motivo: Motivo
    documentos: tuple[DocumentoRef, ...]
    mensagem: str

    @property
    def ids_documentos(self) -> tuple[int, ...]:
        return tuple(d.id for d in self.documentos)


def documentos_da_familia(session: Session, familia: str) -> tuple[DocumentoRef, ...]:
    linhas = session.execute(
        select(Document)
        .join(FaultCoverage, FaultCoverage.document_id == Document.id)
        .where(
            FaultCoverage.fault_family == familia,
            Document.status == "indexed",
        )
        .distinct()
    ).scalars().all()

    return tuple(
        DocumentoRef(
            id=d.id,
            titulo=d.title,
            arquivo=d.filename,
            metodo=d.extraction_method,
            paginas=d.pages,
        )
        for d in linhas
    )


def verificar(
    session: Session, familia: str | None, *, e_problema: bool = True
) -> Cobertura:
    """Decide se o sistema pode prescrever. Chamado ANTES do LLM."""
    if familia is None:
        return Cobertura(
            familia=None,
            coberta=False,
            motivo="sem_diagnostico",
            documentos=(),
            mensagem=(
                "O padrao observado nao corresponde de forma consistente a nenhuma "
                "familia do historico. Nao ha diagnostico confiavel, entao nenhuma "
                "acao de manutencao e recomendada. Os eventos similares encontrados "
                "estao disponiveis para analise da equipe tecnica."
            ),
        )

    if not e_problema or familia not in PROBLEM_FAMILIES:
        descricao = FAMILY_DESCRIPTIONS.get(familia, familia)
        return Cobertura(
            familia=familia,
            coberta=False,
            motivo="estado_operacional",
            documentos=(),
            mensagem=(
                f"O padrao corresponde ao estado operacional `{familia}` "
                f"({descricao}), que nao representa uma falha. Nenhuma acao de "
                "manutencao e indicada."
            ),
        )

    documentos = documentos_da_familia(session, familia)
    if not documentos:
        descricao = FAMILY_DESCRIPTIONS.get(familia, familia)
        return Cobertura(
            familia=familia,
            coberta=False,
            motivo="sem_documento",
            documentos=(),
            mensagem=(
                f"O problema identificado foi `{familia}` ({descricao}), mas ainda "
                "nao existe documentacao cadastrada para esse defeito. O sistema "
                "nao emite recomendacao sem procedimento documentado.\n\n"
                "Registre um novo documento para este defeito em "
                "POST /api/v1/upload_doc para que futuras ocorrencias recebam "
                "orientacao de correcao."
            ),
        )

    titulos = ", ".join(d.titulo for d in documentos)
    return Cobertura(
        familia=familia,
        coberta=True,
        motivo="coberto",
        documentos=documentos,
        mensagem=f"Documentacao disponivel: {titulos}.",
    )


def mapa_de_cobertura(session: Session) -> dict[str, tuple[DocumentoRef, ...]]:
    """Familia -> documentos, para todas as familias de problema da taxonomia."""
    return {familia: documentos_da_familia(session, familia) for familia in sorted(PROBLEM_FAMILIES)}


def familias_descobertas(session: Session) -> list[str]:
    return [f for f, docs in mapa_de_cobertura(session).items() if not docs]
