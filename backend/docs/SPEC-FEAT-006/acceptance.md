# SPEC-FEAT-006 — Critérios de aceite

**Feature:** Extração de texto e OCR dos documentos  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Detecção de camada de texto acerta os 6 arquivos**
  - *Verificação:* Doc2–Doc6 são classificados como `text`; Doc1 é classificado como `ocr`.

- [ ] **Doc1 produz texto útil**
  - *Verificação:* As 17 páginas geram texto legível e a falha-alvo do documento é identificada e registrada em `backend/docs/analise/documentos.md`.

- [ ] **Proveniência completa**
  - *Verificação:* Todo `ExtractedPage` tem `document`, `page` e `method` preenchidos; nenhum trecho anônimo.

- [ ] **Páginas de OCR ruim são sinalizadas**
  - *Verificação:* Página com confiança abaixo do limiar entra no relatório de revisão em vez de ser aceita em silêncio.

- [ ] **Cache evita retrabalho**
  - *Verificação:* Segunda execução da extração não faz nenhuma chamada ao provider de visão.

- [ ] **Títulos de seção sobrevivem à normalização**
  - *Verificação:* Os cabeçalhos numerados (ex.: `3. Sintomas Comuns`) permanecem no texto — são as fronteiras de chunk da SPEC-FEAT-007.
