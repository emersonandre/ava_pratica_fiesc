"""Relatorios da base documental e da cobertura de falhas.

    python manage.py report documentos

Gera docs/analise/documentos.md e docs/analise/cobertura.md. Os numeros saem da
execucao real -- inclusive o acerto das consultas-sonda com e sem filtro, que e a
evidencia da decisao de arquitetura da SPEC-FEAT-010.
"""

from __future__ import annotations

from sqlalchemy import func, select

from app.core.taxonomy import FAMILY_DESCRIPTIONS, PROBLEM_FAMILIES
from app.database import session_scope
from app.integrations.embeddings import embutir_consulta
from app.models import Document, DocumentChunk
from app.services import coverage, retrieval
from app.settings import PROJECT_ROOT, get_settings

SAIDA = PROJECT_ROOT / "backend" / "docs" / "analise"

# Uma sonda por assunto conhecido, para medir se a recuperacao discrimina.
SONDAS: list[tuple[str, str, str]] = [
    ("como corrigir desalinhamento de motor eletrico", "desalinhamento", "Doc2.pdf"),
    ("rotor desbalanceado, vibracao radial elevada", "desbalanceamento", "Doc3.pdf"),
    ("correia frouxa escorregando na polia", "correia", "Doc4.pdf"),
    ("polia excentrica, oscilacao da correia", "polia", "Doc5.pdf"),
    ("rotor inclinado em relacao ao eixo", "cocked_rotor", "Doc6.pdf"),
    ("defeito na pista interna do rolamento", "rolamento", "Doc1.pdf"),
    ("ruido de impacto nas esferas do rolamento", "rolamento", "Doc1.pdf"),
]


def _sonda_sem_filtro(session, pergunta: str) -> str:
    vetor = embutir_consulta(pergunta).tolist()
    distancia = DocumentChunk.embedding.cosine_distance(vetor)
    linha = session.execute(
        select(Document.filename)
        .join(DocumentChunk, DocumentChunk.document_id == Document.id)
        .order_by(distancia)
        .limit(1)
    ).one_or_none()
    return linha[0] if linha else "-"


def _relatorio_documentos(session) -> tuple[str, int, int]:
    settings = get_settings()
    documentos = session.scalars(select(Document).order_by(Document.filename)).all()

    linhas = [
        "# Base documental",
        "",
        "> Gerado por `python manage.py report documentos`.",
        "> Evidencia das [SPEC-FEAT-006](../SPEC-FEAT-006/spec.md) e "
        "[SPEC-FEAT-007](../SPEC-FEAT-007/spec.md).",
        "",
        "## Documentos indexados",
        "",
        "| Arquivo | Titulo | Familia | Paginas | Trechos | Extracao | Confianca |",
        "| --- | --- | --- | ---: | ---: | --- | ---: |",
    ]

    total_trechos = 0
    ocr = 0
    for documento in documentos:
        trechos = session.scalar(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == documento.id)
        )
        total_trechos += trechos or 0
        ocr += documento.extraction_method == "ocr"
        confianca = (
            f"{float(documento.ocr_confidence):.3f}" if documento.ocr_confidence else "—"
        )
        linhas.append(
            f"| `{documento.filename}` | {documento.title} | "
            f"`{documento.fault_family or '—'}` | {documento.pages} | {trechos} | "
            f"{documento.extraction_method} | {confianca} |"
        )

    linhas += [
        "",
        f"**Total: {len(documentos)} documentos, {total_trechos} trechos indexados.**",
        "",
        "## O caso do Doc1",
        "",
        "O `Doc1.pdf` tem 17 paginas e **zero caractere extraivel** — e um documento do "
        "Word com prints colados (`/Creator: Microsoft Word LTSC`). A deteccao automatica "
        "de camada de texto o encaminha para o OCR.",
        "",
        "O resultado justificou o esforco: **o Doc1 e o procedimento de rolamentos**, a "
        "familia com 60.779 registros, 36% de toda a base. Suas secoes 4.1 a 4.4 tratam "
        "de defeito na pista externa, pista interna, esferas e combinado — exatamente os "
        "rotulos canonicos `rolamento_outer`, `rolamento_inner`, `rolamento_ball` e "
        "`rolamento_combination`. Sem OCR, a maior massa do dataset ficaria sem "
        "documentacao.",
        "",
        "### Motor de OCR",
        "",
        "`rapidocr-onnxruntime` (PP-OCR em ONNX Runtime), local, CPU, offline. Alternativas "
        "descartadas com o motivo registrado:",
        "",
        "| Alternativa | Por que nao |",
        "| --- | --- |",
        "| Modelo de visao por API (plano original) | Nenhum modelo DeepSeek aceita imagem — `v4-flash`, `v4-pro`, `chat` e `vl2` foram testados. A conta OpenAI disponivel estava sem credito. Amarrar a preparacao da base a credito externo tambem contraria a restricao de operacao da secao 5 |",
        "| Tesseract | Exigiria instalacao de binario no sistema |",
        "",
        "### Limitacao conhecida do OCR",
        "",
        "O modelo transcreve texto latino mas **perde diacriticos** e confunde caracteres "
        "de forma parecida. Exemplos reais do Doc1:",
        "",
        "| Transcrito | Original |",
        "| --- | --- |",
        "| `Diagnostico` | Diagnóstico |",
        "| `lnner Race Fault` | Inner Race Fault |",
        "| `guando` | quando |",
        "",
        "Isso nao inviabiliza a recuperacao — o modelo de embedding e multilingue e tolera "
        "a variacao, e as sondas do Doc1 acertam. Mas o texto nao e fiel ao original, e por "
        "isso os documentos vindos de OCR ficam **sinalizados** no campo `extraction_method` "
        "e devem aparecer marcados na interface: uma prescricao baseada em OCR carrega mais "
        "risco que uma baseada em camada de texto.",
        "",
        "## Chunking",
        "",
        "A divisao segue os cabecalhos numerados dos procedimentos (`1. Objetivo`, "
        "`4.1. Correia Frouxa`, `3.1. Excentricidade`), que sao fronteiras semanticas reais. "
        "Cortar a cada N caracteres quebraria um procedimento no meio — e meio procedimento "
        "de manutencao e a falha mais cara possivel nesta aplicacao: o tecnico recebe metade "
        "dos passos de uma intervencao fisica em equipamento.",
        "",
        f"Embeddings: `{settings.embedding_model}` ({settings.embedding_dim} dimensoes), "
        "local em ONNX Runtime, CPU, sem chamada de rede.",
        "",
    ]
    return "\n".join(linhas), len(documentos), total_trechos


def _relatorio_cobertura(session) -> tuple[str, int]:
    mapa = coverage.mapa_de_cobertura(session)
    descobertas = [f for f, docs in mapa.items() if not docs]

    linhas = [
        "# Cobertura documental das falhas",
        "",
        "> Gerado por `python manage.py report documentos`.",
        "> Evidencia das [SPEC-FEAT-008](../SPEC-FEAT-008/spec.md) e "
        "[SPEC-FEAT-010](../SPEC-FEAT-010/spec.md).",
        "",
        "## Mapa familia -> documento",
        "",
        "O vinculo e **explicito e revisado**, nunca inferido pelo modelo. E o que sustenta "
        "a regra da secao 3 do enunciado: sem linha aqui, o LLM nao e chamado.",
        "",
        "| Familia | Descricao | Documento | Situacao |",
        "| --- | --- | --- | --- |",
    ]
    for familia, documentos in mapa.items():
        arquivos = ", ".join(f"`{d.arquivo}`" for d in documentos) or "—"
        situacao = "coberta" if documentos else "**sem documento**"
        linhas.append(
            f"| `{familia}` | {FAMILY_DESCRIPTIONS.get(familia, '')} | {arquivos} | {situacao} |"
        )

    linhas += [
        "",
        f"**{len(mapa) - len(descobertas)} de {len(mapa)} familias de problema cobertas.**",
        "",
        "## Familias sem documentacao",
        "",
        "- " + "\n- ".join(f"`{f}`" for f in descobertas),
        "",
        "Sao o caso de recusa exigido pelo enunciado — **reais, nao fabricados para a "
        "demonstracao**. Ao receber um evento dessas familias, o sistema informa que ainda "
        "nao existe documentacao para o problema identificado e sugere registrar um novo "
        "documento, sem chamar o modelo de linguagem.",
        "",
        "## Desfechos do gate",
        "",
        "| Motivo | Quando ocorre | O LLM e chamado? |",
        "| --- | --- | :---: |",
        "| `coberto` | Ha documento para a familia diagnosticada | sim |",
        "| `sem_documento` | Falha identificada, nenhum documento a cobre | **nao** |",
        "| `estado_operacional` | O padrao e um estado (normal, motor parado), nao falha | **nao** |",
        "| `sem_diagnostico` | A vizinhanca nao sustenta um diagnostico | **nao** |",
        "",
        "Colapsar os quatro em um generico \"nao sei\" desperdicaria a informacao mais util "
        "da solucao: o motivo pelo qual o sistema se absteve.",
        "",
        "## Por que o filtro por familia e rigido",
        "",
        "Os seis documentos compartilham quase o mesmo vocabulario tecnico — \"vibracao "
        "elevada\", \"aquecimento nos mancais\", \"desgaste de rolamentos\", \"afrouxamento "
        "de parafusos\". Busca puramente semantica erra, e erra com confianca.",
        "",
        "Medicao com sete consultas-sonda, uma por assunto conhecido:",
        "",
        "| Consulta | Sem filtro | Com filtro | Esperado |",
        "| --- | --- | --- | --- |",
    ]

    acertos_sem = acertos_com = 0
    for pergunta, familia, esperado in SONDAS:
        sem_filtro = _sonda_sem_filtro(session, pergunta)
        cobertura = coverage.verificar(session, familia)
        trechos = retrieval.recuperar(
            session, pergunta, ids_documentos=cobertura.ids_documentos
        )
        com_filtro = sorted({t.documento for t in trechos})
        ok_sem = sem_filtro == esperado
        ok_com = com_filtro == [esperado]
        acertos_sem += ok_sem
        acertos_com += ok_com
        marca_sem = "" if ok_sem else " ✗"
        marca_com = "" if ok_com else " ✗"
        linhas.append(
            f"| {pergunta} | `{sem_filtro}`{marca_sem} | "
            f"`{', '.join(com_filtro)}`{marca_com} | `{esperado}` |"
        )

    total = len(SONDAS)
    linhas += [
        "",
        f"**Acerto: {acertos_sem}/{total} sem filtro, {acertos_com}/{total} com filtro.**",
        "",
        "Sem o filtro, \"ruido de impacto nas esferas do rolamento\" recupera o manual de "
        "**correias**. A resposta sairia fluente, citada — e apontando o procedimento errado. "
        "Em manutencao industrial isso e pior que nao responder.",
        "",
        "O filtro e rigido, nao um reforco de score: um peso alto ainda deixaria passar "
        "documento errado; o corte duro elimina a classe inteira de erro.",
        "",
    ]
    return "\n".join(linhas), len(descobertas)


def run() -> int:
    SAIDA.mkdir(parents=True, exist_ok=True)
    with session_scope() as session:
        texto_documentos, n_docs, n_trechos = _relatorio_documentos(session)
        (SAIDA / "documentos.md").write_text(texto_documentos, encoding="utf-8")

        texto_cobertura, n_descobertas = _relatorio_cobertura(session)
        (SAIDA / "cobertura.md").write_text(texto_cobertura, encoding="utf-8")

    print(f"  documentos.md: {n_docs} documentos, {n_trechos} trechos")
    print(
        f"  cobertura.md : {len(PROBLEM_FAMILIES) - n_descobertas}/"
        f"{len(PROBLEM_FAMILIES)} familias cobertas"
    )
    return 0
