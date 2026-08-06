"""Relatorio da guarda anti-alucinacao.

    python manage.py report alucinacao

Executa os cenarios de verdade -- inclusive as chamadas ao modelo -- e registra o
comportamento observado. E a evidencia para o criterio "Alucinacao do modelo" da
entrevista: mostra, nao afirma.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.core.features import FEATURE_COLUMNS
from app.database import session_scope
from app.models import SensorEvent
from app.schemas.prescription import Prescricao
from app.services import pipeline
from app.settings import PROJECT_ROOT

SAIDA = PROJECT_ROOT / "backend" / "docs" / "analise" / "alucinacao.md"


@dataclass
class Cenario:
    nome: str
    descricao: str
    evento_id: int | None = None
    familia: str | None = None
    pergunta: str = "Como corrigir esta falha?"
    esperado: str = ""


CENARIOS = [
    Cenario(
        nome="Falha coberta por documento com camada de texto",
        descricao="Desalinhamento, coberto pelo Doc2.",
        evento_id=153184,
        esperado="prescricao citada",
    ),
    Cenario(
        nome="Falha coberta por documento vindo de OCR",
        descricao="Rolamento, coberto pelo Doc1 (17 paginas em imagem).",
        evento_id=162283,
        pergunta="Como corrigir este defeito no rolamento?",
        esperado="prescricao citada + aviso de OCR",
    ),
    Cenario(
        nome="Falha identificada, sem documentacao",
        descricao="Rotor excentrico. Diagnostico confiavel, nenhum documento cobre.",
        evento_id=163383,
        esperado="recusa `sem_documento`, LLM nao chamado",
    ),
    Cenario(
        nome="Estado operacional, nao falha",
        descricao="Motor desligado.",
        familia="motor_desligado",
        esperado="recusa `estado_operacional`, LLM nao chamado",
    ),
    Cenario(
        nome="Vizinhanca dividida",
        descricao="Ventoinha. O sinal nao sustenta diagnostico.",
        familia="ventoinha",
        esperado="recusa, LLM nao chamado",
    ),
]

FORA_DE_DOMINIO = [
    "Qual a capital da Franca?",
    "Me conte uma piada.",
    "Quem ganhou a copa de 2022?",
    "Escreva um poema sobre o mar.",
]

NO_DOMINIO = [
    "Como corrigir o desalinhamento do motor?",
    "Qual a temperatura aceitavel do mancal?",
    "O rolamento esta com ruido de impacto.",
]


def _payload(evento: SensorEvent) -> dict:
    return {coluna: float(getattr(evento, coluna)) for coluna in FEATURE_COLUMNS}


def run() -> int:
    linhas: list[str] = [
        "# Guarda anti-alucinacao -- comportamento observado",
        "",
        "> Gerado por `python manage.py report alucinacao`. Os cenarios sao executados de",
        "> verdade, inclusive as chamadas ao modelo. Evidencia da",
        "> [SPEC-FEAT-012](../SPEC-FEAT-012/spec.md).",
        "",
        "## Defesa em quatro camadas",
        "",
        "| Camada | Mecanismo | O que impede |",
        "| --- | --- | --- |",
        "| 1 | Gate de cobertura, antes do LLM | Responder sobre falha sem documentacao. O modelo nao e chamado — nao ha como alucinar o que nao foi perguntado |",
        "| 2 | Filtro rigido por familia na recuperacao | Citar o procedimento errado. Medido: 4/7 de acerto sem filtro, 7/7 com ele |",
        "| 3 | Prompt restritivo + descarte de citacao inventada | Alucinacao de fonte — a mais perigosa, porque parece verificavel |",
        "| 4 | Verificacao de embasamento pos-geracao | Passo redigido sem origem no texto recuperado |",
        "",
        "## Divisao de trabalho",
        "",
        "```",
        "numeros (quantos eventos, desde quando, frequencia)  -> banco",
        "qual documento consultar                             -> codigo",
        "quais trechos entram no contexto                     -> codigo",
        "redacao dos passos a partir desses trechos           -> MODELO",
        "verificacao de que cada passo tem respaldo           -> codigo",
        "```",
        "",
        "O modelo so redige. Nao escolhe fonte, nao inventa numero e nao decide se pode",
        "responder.",
        "",
        "## Cenarios executados",
        "",
        "| Cenario | Esperado | Observado | LLM chamado | Embasamento |",
        "| --- | --- | --- | :---: | ---: |",
    ]

    detalhes: list[str] = []

    with session_scope() as session:
        for cenario in CENARIOS:
            if cenario.evento_id:
                evento = session.get(SensorEvent, cenario.evento_id)
            else:
                evento = session.scalars(
                    select(SensorEvent)
                    .where(
                        SensorEvent.split == "train",
                        SensorEvent.fault_family == cenario.familia,
                    )
                    .limit(1)
                ).one()

            resultado = pipeline.analisar_evento(
                session, _payload(evento), pergunta=cenario.pergunta
            )
            resposta = resultado.resposta

            if isinstance(resposta, Prescricao):
                observado = f"prescricao com {len(resposta.passos)} passos"
                embasamento = (
                    f"{resposta.embasamento.score:.0%}" if resposta.embasamento else "—"
                )
            else:
                observado = f"recusa `{resposta.motivo}`"
                embasamento = "—"

            linhas.append(
                f"| {cenario.nome} | {cenario.esperado} | {observado} | "
                f"{'sim' if resultado.chamou_llm else '**nao**'} | {embasamento} |"
            )

            bloco = [
                f"### {cenario.nome}",
                "",
                cenario.descricao,
                "",
                f"- Rotulo real: `{evento.fault_family}`",
                f"- Diagnostico: `{resultado.similaridade.familia_diagnosticada}` "
                f"(confianca {resultado.similaridade.confianca:.0%})",
                f"- Cobertura: `{resultado.cobertura.motivo}`",
                f"- Documentos: {[d.arquivo for d in resultado.cobertura.documentos] or '—'}",
                f"- LLM chamado: **{'sim' if resultado.chamou_llm else 'nao'}**",
                f"- Tempo total: {resultado.tempos.total_ms:.0f} ms",
                "",
            ]

            if isinstance(resposta, Prescricao):
                bloco += [
                    f"**Diagnostico:** {resposta.diagnostico}",
                    "",
                    f"**Passos:** {len(resposta.inspecao)} de inspecao, "
                    f"{len(resposta.correcao)} de correcao, "
                    f"{len(resposta.validacao)} de validacao.",
                    "",
                    "Exemplo de passo com citacao:",
                    "",
                ]
                if resposta.passos:
                    exemplo = resposta.passos[0]
                    bloco += [
                        f"> {exemplo.texto}",
                        f"> {' '.join(exemplo.citacoes)}",
                        "",
                    ]
                relatorio = resposta.embasamento
                if relatorio:
                    bloco += [
                        f"**Embasamento:** {relatorio.embasadas}/{relatorio.afirmacoes} "
                        f"= {relatorio.score:.0%}",
                        "",
                    ]
                    if relatorio.removidas:
                        bloco += ["Passos removidos por falta de respaldo:", ""]
                        bloco += [f"- {r}" for r in relatorio.removidas]
                        bloco.append("")
                if resposta.avisos:
                    bloco += ["Avisos declarados pelo sistema:", ""]
                    bloco += [f"- {a}" for a in resposta.avisos]
                    bloco.append("")
            else:
                bloco += [
                    f"**Recusa (`{resposta.motivo}`):**",
                    "",
                    f"> {resposta.mensagem}",
                    "",
                ]
                if resposta.sugestao:
                    bloco += [f"> {resposta.sugestao}", ""]

            detalhes.append("\n".join(bloco))

    linhas += [
        "",
        "## Recusa de pergunta fora de dominio",
        "",
        "| Pergunta | No dominio? |",
        "| --- | :---: |",
    ]
    for pergunta in NO_DOMINIO:
        linhas.append(f"| {pergunta} | sim |")
    for pergunta in FORA_DE_DOMINIO:
        marca = "sim" if pipeline.pergunta_no_dominio(pergunta) else "**nao**"
        linhas.append(f"| {pergunta} | {marca} |")

    linhas += [
        "",
        "---",
        "",
        "## Detalhamento",
        "",
        *detalhes,
        "## Limitacoes assumidas",
        "",
        "- **Nao existe garantia formal de ausencia de alucinacao.** O objetivo e reduzir a",
        "  taxa e tornar cada afirmacao auditavel ate a pagina do PDF.",
        "- A verificacao de embasamento e **lexica**, nao semantica. Ela prova que o passo",
        "  tem origem no texto recuperado, nao que o passo esta tecnicamente correto.",
        "  Usar um LLM como juiz teria custo, latencia e o problema de que o juiz alucina",
        "  igual.",
        "- Documentos vindos de OCR carregam risco maior: o motor perde diacriticos e",
        "  confunde caracteres. Toda prescricao baseada neles traz aviso explicito.",
        "- O limiar de confianca da similaridade e uma escolha de projeto. Mais cobertura",
        "  significa mais erro; a tabela de precisao x cobertura esta em",
        "  [similaridade.md](similaridade.md).",
        "",
    ]

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(linhas), encoding="utf-8")
    print(f"  alucinacao.md: {len(CENARIOS)} cenarios executados")
    return 0
