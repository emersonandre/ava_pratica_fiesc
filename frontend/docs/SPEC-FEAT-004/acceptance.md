# SPEC-FEAT-004 — Critérios de aceite

**Feature:** Gestão de documentos  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Lista reflete o backend**
  - *Verificação:* Documentos, páginas e contagem de chunks batem com `/api/documents`.

- [ ] **OCR é sinalizado**
  - *Verificação:* O documento processado por OCR aparece marcado como tal na lista.

- [ ] **Upload dá retorno claro**
  - *Verificação:* Durante o processamento há indicação de progresso; ao final, sucesso com contagem de chunks ou erro com motivo.

- [ ] **Lacunas viram ação**
  - *Verificação:* Cada família sem documento tem um botão que abre o upload já com a família preenchida.

- [ ] **Cobertura atualiza na hora**
  - *Verificação:* Após upload bem-sucedido, a lista e o painel de lacunas se atualizam sem recarregar a página.

- [ ] **Arquivo inválido é barrado com clareza**
  - *Verificação:* Enviar um não-PDF mostra mensagem específica, sem deixar a interface em estado de carregamento infinito.
