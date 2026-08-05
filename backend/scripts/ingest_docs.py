"""Indexa os documentos fornecidos pela empresa.

    python manage.py ingest-docs

## Mapa de cobertura

O vinculo familia -> documento e explicito e revisado, nunca inferido pelo LLM.
E a regra de negocio da secao 3 do enunciado ("o sistema deve se deter unicamente
a problemas que possuem documentos"), e regra de negocio nao se implementa como
pedido educado no prompt.

O Doc1 so revelou seu assunto depois do OCR: as 17 paginas em imagem sao o
procedimento de **rolamentos** -- a familia com 60.779 registros, 36% da base.
Sem OCR, a maior massa do dataset ficaria sem documentacao.

Familias que seguem descobertas depois desta indexacao: `eccentric_rotor`,
`ventoinha` e `falta_fase`. Sao o caso real de recusa exigido pelo enunciado --
nao um cenario fabricado para a demonstracao.
"""

from __future__ import annotations

from app.database import session_scope
from app.services.document_indexing import (
    indexar,
    registrar_metadado_do_indice,
    vincular_cobertura,
)
from app.settings import get_settings

# Vinculo revisado manualmente a partir da leitura de cada documento.
COBERTURA: dict[str, tuple[str, str, str]] = {
    "Doc1.pdf": (
        "rolamento",
        "Procedimento para Diagnostico e Correcao de Problemas em Rolamentos",
        "Secoes 4.1 a 4.4 tratam de defeito na pista externa, pista interna, "
        "esferas e combinado -- correspondem aos canonicos rolamento_outer, "
        "rolamento_inner, rolamento_ball e rolamento_combination.",
    ),
    "Doc2.pdf": (
        "desalinhamento",
        "Procedimento para Correcao de Desalinhamento em Motor Eletrico",
        "Secao 2 descreve desalinhamento paralelo, angular e combinado.",
    ),
    "Doc3.pdf": (
        "desbalanceamento",
        "Procedimento para Correcao de Desbalanceamento em Maquinas Rotativas",
        "Secao 2 traz a formulacao F = m x r x omega^2 e a secao 4 as causas.",
    ),
    "Doc4.pdf": (
        "correia",
        "Procedimento para Diagnostico e Correcao de Problemas em Correias",
        "Secao 4 cobre correia frouxa, tensionada em excesso e desgastada.",
    ),
    "Doc5.pdf": (
        "polia",
        "Procedimento para Diagnostico e Correcao de Problemas em Polias",
        "Secao 3 cobre excentricidade, desbalanceamento e desgaste de polia.",
    ),
    "Doc6.pdf": (
        "cocked_rotor",
        "Procedimento para Diagnostico e Correcao de Rotor Inclinado (Cocked Rotor)",
        "Documento dedicado a condicao de rotor inclinado.",
    ),
}


def run(*, forcar: bool = False) -> int:
    settings = get_settings()
    diretorio = settings.documents_path
    arquivos = sorted(diretorio.glob("*.pdf"))

    if not arquivos:
        print(f"nenhum PDF em {diretorio}")
        return 1

    print(f"origem         {diretorio}")
    total_trechos = 0

    with session_scope() as session:
        registrar_metadado_do_indice(session)

        for caminho in arquivos:
            familia, titulo, evidencia = COBERTURA.get(caminho.name, (None, caminho.stem, None))
            resultado = indexar(session, caminho, familia=familia, titulo=titulo, forcar=forcar)
            documento = resultado.documento

            if documento.status == "failed":
                print(f"  {caminho.name:10s} FALHOU  {documento.error}")
                continue

            if familia:
                vincular_cobertura(
                    session, familia, documento, origem="manual", evidencia=evidencia
                )

            marca = "(ja indexado)" if resultado.ja_existia else ""
            confianca = (
                f" conf={float(documento.ocr_confidence):.3f}" if documento.ocr_confidence else ""
            )
            print(
                f"  {caminho.name:10s} {documento.extraction_method:4s} "
                f"paginas={documento.pages:2d} trechos={resultado.trechos:3d}"
                f"{confianca}  -> {familia or 'sem familia'} {marca}"
            )
            total_trechos += resultado.trechos

    print(f"\ntrechos        {total_trechos}")
    return 0
