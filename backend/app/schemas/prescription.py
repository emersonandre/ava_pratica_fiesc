"""Contratos da resposta prescritiva.

Saida estruturada, nao texto corrido. Tres motivos:

1. permite verificar embasamento campo a campo (SPEC-FEAT-012);
2. o operador em chao de fabrica segue passos numerados, nao paragrafos;
3. reduz divagacao -- o modelo preenche campos, nao redige livremente.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TipoResposta = Literal["prescricao", "recusa"]


class Citacao(BaseModel):
    documento: str = Field(description="Arquivo de origem, ex.: Doc2.pdf")
    pagina_inicial: int
    pagina_final: int
    secao: str | None = None
    metodo: str = Field(description="`text` ou `ocr` -- OCR carrega mais risco")

    @property
    def rotulo(self) -> str:
        if self.pagina_inicial == self.pagina_final:
            return f"[{self.documento}, p. {self.pagina_inicial}]"
        return f"[{self.documento}, p. {self.pagina_inicial}-{self.pagina_final}]"


class Passo(BaseModel):
    texto: str
    citacoes: list[str] = Field(
        default_factory=list,
        description="Rotulos de citacao, ex.: ['[Doc2.pdf, p. 4]']",
    )


class RelatorioEmbasamento(BaseModel):
    """Resultado da verificacao pos-geracao (SPEC-FEAT-012)."""

    afirmacoes: int
    embasadas: int
    removidas: list[str] = Field(default_factory=list)
    score: float = Field(description="embasadas / afirmacoes, em [0, 1]")
    verificado: bool = Field(
        description="False quando a verificacao nao pode ser executada"
    )


class Prescricao(BaseModel):
    tipo: TipoResposta = "prescricao"
    diagnostico: str
    inspecao: list[Passo] = Field(default_factory=list)
    correcao: list[Passo] = Field(default_factory=list)
    validacao: list[Passo] = Field(default_factory=list)
    citacoes: list[Citacao] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list)
    embasamento: RelatorioEmbasamento | None = None

    @property
    def passos(self) -> list[Passo]:
        return [*self.inspecao, *self.correcao, *self.validacao]


class Recusa(BaseModel):
    """Resposta quando o sistema nao pode prescrever.

    O motivo vem do gate de cobertura, que roda ANTES do LLM. Nesta resposta
    nenhum texto foi gerado por modelo de linguagem.
    """

    tipo: TipoResposta = "recusa"
    motivo: Literal[
        "sem_documento", "estado_operacional", "sem_diagnostico", "fora_de_dominio"
    ]
    mensagem: str
    familia: str | None = None
    sugestao: str | None = None
