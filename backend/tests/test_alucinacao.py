"""SPEC-FEAT-012 -- suite adversarial contra alucinacao.

"Alucinacao do modelo" e criterio explicito da entrevista. Estes testes existem
para **mostrar** o comportamento, nao para afirma-lo.

A maioria nao chama o modelo de linguagem: o ponto e justamente provar que, nos
casos de recusa, ele **nao e chamado**. Os que precisam de geracao real ficam
marcados com `llm` e sao pulados por padrao -- rode com `pytest -m llm`.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.features import FEATURE_COLUMNS
from app.models import SensorEvent
from app.schemas.prescription import Passo, Prescricao, Recusa
from app.services import grounding, pipeline, prescription, retrieval
from app.services.retrieval import TrechoRecuperado
from tests.conftest import precisa_banco

pytestmark = precisa_banco

# Eventos escolhidos por passarem o gate de confianca, para exercitar cada
# desfecho de forma deterministica.
EVENTO_COBERTO = 153184  # desalinhamento, confianca 86%, coberto pelo Doc2
EVENTO_SEM_DOCUMENTO = 163383  # eccentric_rotor, confianca 70%, sem documento


def payload_de(evento: SensorEvent) -> dict:
    return {coluna: float(getattr(evento, coluna)) for coluna in FEATURE_COLUMNS}


@pytest.fixture
def espiao_llm(monkeypatch):
    """Registra qualquer chamada ao provider. Falha o teste se houver alguma."""
    chamadas: list[str] = []

    def _proibido(*_args, **_kwargs):
        chamadas.append("completar")
        raise AssertionError("o LLM foi chamado quando nao deveria")

    monkeypatch.setattr(prescription, "get_provider", lambda: _FakeProvider(_proibido))
    return chamadas


class _FakeProvider:
    def __init__(self, funcao) -> None:
        self._funcao = funcao

    def completar(self, *args, **kwargs):
        return self._funcao(*args, **kwargs)


# --- Camada 1: gate de cobertura ---------------------------------------------
def test_familia_sem_documento_nao_chama_o_llm(session, base_populada, espiao_llm) -> None:
    """O caso real do enunciado: falha identificada, documentacao inexistente."""
    evento = session.get(SensorEvent, EVENTO_SEM_DOCUMENTO)
    resultado = pipeline.analisar_evento(session, payload_de(evento))

    assert isinstance(resultado.resposta, Recusa)
    assert resultado.resposta.motivo == "sem_documento"
    assert resultado.chamou_llm is False
    assert not espiao_llm, "o gate deveria ter interrompido antes do modelo"


def test_recusa_sugere_registrar_documento(session, base_populada) -> None:
    """Secao 3 do enunciado: sugerir ao usuario registrar um novo documento."""
    evento = session.get(SensorEvent, EVENTO_SEM_DOCUMENTO)
    resposta = pipeline.analisar_evento(session, payload_de(evento)).resposta

    assert isinstance(resposta, Recusa)
    assert "documenta" in resposta.mensagem.lower()
    assert resposta.sugestao and "upload_doc" in resposta.sugestao


def test_recusa_ainda_entrega_a_evidencia(session, base_populada) -> None:
    """Recusar nao e devolver nada: a analise estatistica continua disponivel."""
    evento = session.get(SensorEvent, EVENTO_SEM_DOCUMENTO)
    resultado = pipeline.analisar_evento(session, payload_de(evento))

    assert resultado.similaridade.vizinhos
    assert resultado.similaridade.evidencia is not None
    assert resultado.similaridade.evidencia.linha_do_tempo


def test_estado_operacional_nao_gera_prescricao(session, base_populada, espiao_llm) -> None:
    evento = session.scalars(
        select(SensorEvent)
        .where(SensorEvent.split == "train", SensorEvent.fault_family == "motor_desligado")
        .limit(1)
    ).one()
    resultado = pipeline.analisar_evento(session, payload_de(evento))

    assert isinstance(resultado.resposta, Recusa)
    assert resultado.resposta.motivo == "estado_operacional"
    assert not espiao_llm


def test_vizinhanca_dividida_nao_chama_o_llm(session, base_populada, espiao_llm) -> None:
    evento = session.scalars(
        select(SensorEvent)
        .where(SensorEvent.split == "train", SensorEvent.fault_family == "ventoinha")
        .limit(1)
    ).one()
    resultado = pipeline.analisar_evento(session, payload_de(evento))

    assert isinstance(resultado.resposta, Recusa)
    assert resultado.resposta.motivo in {"sem_diagnostico", "sem_documento"}
    assert not espiao_llm


# --- Camada 2: filtro por familia --------------------------------------------
def test_recuperacao_sem_cobertura_levanta(session, base_populada) -> None:
    """Chamar o retriever sem documentos e erro de programacao, nao caso valido."""
    with pytest.raises(retrieval.SemCobertura):
        retrieval.recuperar(session, "como corrigir", ids_documentos=())


def test_pergunta_fora_de_dominio_e_detectada() -> None:
    """O filtro peca para o lado permissivo: falso negativo custa mais que falso
    positivo, porque o gate e o embasamento seguram o resto."""
    no_dominio = [
        "como corrigir o desalinhamento do motor",
        "qual a temperatura aceitavel do mancal",
        "que ferramentas eu preciso?",
        "como confirmo que resolveu?",
        "quais os cuidados de seguranca?",
        "com que frequencia devo acompanhar?",
        "o que causa esse defeito?",
    ]
    for pergunta in no_dominio:
        assert pipeline.pergunta_no_dominio(pergunta), pergunta

    fora = [
        "qual a capital da Franca?",
        "me conte uma piada",
        "quem ganhou a copa de 2022",
        "escreva um poema sobre o mar",
    ]
    for pergunta in fora:
        assert not pipeline.pergunta_no_dominio(pergunta), pergunta


# --- Camada 3: citacao inventada ---------------------------------------------
def _trecho(rotulo_doc: str, pagina: int, conteudo: str) -> TrechoRecuperado:
    return TrechoRecuperado(
        documento=rotulo_doc,
        documento_id=1,
        titulo="doc",
        metodo="text",
        pagina_inicial=pagina,
        pagina_final=pagina,
        secao=None,
        conteudo=conteudo,
        score=0.9,
    )


def test_citacao_inexistente_e_descartada() -> None:
    """Alucinacao de FONTE e a mais perigosa: parece verificavel."""
    validos = {"[Doc2.pdf, p. 4]"}
    passos = prescription._montar_passos(
        [
            {"texto": "Alinhe o eixo.", "citacoes": ["[Doc2.pdf, p. 4]"]},
            {"texto": "Aplique torque de 90 Nm.", "citacoes": ["[Doc9.pdf, p. 99]"]},
        ],
        validos,
    )
    assert passos[0].citacoes == ["[Doc2.pdf, p. 4]"]
    assert passos[1].citacoes == [], "citacao inventada deveria ter sido removida"


# --- Camada 4: verificacao de embasamento ------------------------------------
def test_passo_sem_citacao_e_removido() -> None:
    trechos = [_trecho("Doc2.pdf", 4, "Afrouxe os parafusos e insira calcos calibrados.")]
    prescricao = Prescricao(
        diagnostico="desalinhamento",
        correcao=[
            Passo(texto="Afrouxe os parafusos e insira calcos calibrados.",
                  citacoes=["[Doc2.pdf, p. 4]"]),
            Passo(texto="Troque o motor por um modelo novo.", citacoes=[]),
        ],
    )
    saneada, relatorio = grounding.verificar(prescricao, trechos)

    assert len(saneada.correcao) == 1
    assert relatorio.afirmacoes == 2
    assert relatorio.embasadas == 1
    assert "sem citacao" in relatorio.removidas[0]


def test_passo_sem_relacao_com_o_trecho_citado_e_removido() -> None:
    """Citar nao basta: o passo precisa ter origem no texto citado."""
    trechos = [_trecho("Doc2.pdf", 4, "Afrouxe os parafusos e insira calcos calibrados.")]
    prescricao = Prescricao(
        diagnostico="desalinhamento",
        correcao=[
            Passo(
                texto="Substitua o inversor de frequencia e reprograme a rampa de partida.",
                citacoes=["[Doc2.pdf, p. 4]"],
            )
        ],
    )
    saneada, relatorio = grounding.verificar(prescricao, trechos)

    assert saneada.correcao == []
    assert relatorio.score == 0.0
    assert "sobreposicao" in relatorio.removidas[0]


def test_reformulacao_legitima_e_preservada() -> None:
    """O modelo reescreve em imperativo; isso nao pode ser punido como alucinacao."""
    trechos = [
        _trecho(
            "Doc2.pdf",
            4,
            "O tecnico deve afrouxar os parafusos de fixacao do motor e inserir "
            "calcos calibrados sob os pes ate atingir a tolerancia de alinhamento.",
        )
    ]
    prescricao = Prescricao(
        diagnostico="desalinhamento",
        correcao=[
            Passo(
                texto="Afrouxe os parafusos de fixacao e insira calcos calibrados "
                "sob os pes ate atingir a tolerancia.",
                citacoes=["[Doc2.pdf, p. 4]"],
            )
        ],
    )
    saneada, relatorio = grounding.verificar(prescricao, trechos)

    assert len(saneada.correcao) == 1
    assert relatorio.score == 1.0


def test_citacoes_refletem_apenas_os_passos_sobreviventes() -> None:
    from app.schemas.prescription import Citacao

    trechos = [
        _trecho("Doc2.pdf", 4, "Afrouxe os parafusos e insira calcos calibrados."),
        _trecho("Doc2.pdf", 5, "Meca a vibracao apos o alinhamento."),
    ]
    prescricao = Prescricao(
        diagnostico="d",
        correcao=[
            Passo(texto="Afrouxe os parafusos e insira calcos.", citacoes=["[Doc2.pdf, p. 4]"])
        ],
        validacao=[Passo(texto="Compre um rolamento novo.", citacoes=["[Doc2.pdf, p. 5]"])],
        citacoes=[
            Citacao(documento="Doc2.pdf", pagina_inicial=4, pagina_final=4, metodo="text"),
            Citacao(documento="Doc2.pdf", pagina_inicial=5, pagina_final=5, metodo="text"),
        ],
    )
    saneada, _ = grounding.verificar(prescricao, trechos)

    rotulos = {c.rotulo for c in saneada.citacoes}
    assert rotulos == {"[Doc2.pdf, p. 4]"}


def test_relatorio_de_embasamento_sempre_presente() -> None:
    trechos = [_trecho("Doc2.pdf", 4, "Afrouxe os parafusos.")]
    prescricao = Prescricao(
        diagnostico="d",
        correcao=[Passo(texto="Afrouxe os parafusos.", citacoes=["[Doc2.pdf, p. 4]"])],
    )
    saneada, relatorio = grounding.verificar(prescricao, trechos)

    assert saneada.embasamento is relatorio
    assert relatorio.verificado is True
    assert 0.0 <= relatorio.score <= 1.0


def test_geracao_sem_trechos_levanta() -> None:
    contexto = prescription.ContextoPrescricao(
        familia="desalinhamento", confianca=0.9, eventos_similares=10, trechos=[]
    )
    with pytest.raises(prescription.GeracaoInvalida, match="gate"):
        prescription.gerar(contexto, "como corrigir")


# --- Testes que chamam o modelo de verdade -----------------------------------
@pytest.mark.llm
def test_falha_coberta_gera_prescricao_citada(session, base_populada) -> None:
    evento = session.get(SensorEvent, EVENTO_COBERTO)
    resultado = pipeline.analisar_evento(
        session, payload_de(evento), pergunta="Como corrigir esta falha?"
    )

    resposta = resultado.resposta
    assert isinstance(resposta, Prescricao)
    assert resposta.passos, "deveria ter produzido passos"
    assert all(passo.citacoes for passo in resposta.passos)

    documentos = {citacao.documento for citacao in resposta.citacoes}
    assert documentos == {"Doc2.pdf"}, "nenhum documento fora da cobertura"

    assert resposta.embasamento is not None
    assert resposta.embasamento.score >= 0.8


@pytest.mark.llm
def test_prescricao_de_documento_ocr_traz_aviso(session, base_populada) -> None:
    evento = session.scalars(
        select(SensorEvent)
        .where(SensorEvent.split == "train", SensorEvent.id == 162283)
        .limit(1)
    ).one()
    resposta = pipeline.analisar_evento(
        session, payload_de(evento), pergunta="Como corrigir este defeito no rolamento?"
    ).resposta

    assert isinstance(resposta, Prescricao)
    assert any("OCR" in aviso for aviso in resposta.avisos)
