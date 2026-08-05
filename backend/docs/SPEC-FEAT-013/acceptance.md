# SPEC-FEAT-013 — Critérios de aceite

**Feature:** API REST  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **OpenAPI publicada e separada por superfície**
  - *Verificação:* `/docs` lista as rotas com schemas de entrada e saída, agrupadas por tag (`v1` e `internal`).

- [ ] **Payload do enunciado funciona sem adaptação**
  - *Verificação:* O JSON de exemplo do §2 é aceito por `/api/v1/predict` exatamente como está.

- [ ] **`/predict` devolve JSON consolidado**
  - *Verificação:* Uma única resposta traz diagnóstico, evidência estatística, cobertura documental, prescrição (ou recusa) e citações — sem exigir chamadas extras.

- [ ] **`/upload_doc` injeta no banco vetorial**
  - *Verificação:* Após o upload, os chunks do documento novo aparecem em `document_chunks` e passam a ser recuperáveis.

- [ ] **Campo faltante gera erro útil**
  - *Verificação:* Payload sem uma feature obrigatória retorna 422 nomeando o campo.

- [ ] **Erro de negócio não vaza stack trace**
  - *Verificação:* Provider indisponível retorna código e mensagem acionáveis, com o stack trace apenas no log.

- [ ] **Tempos por etapa presentes**
  - *Verificação:* Toda resposta de `/predict` traz `timings` com similaridade, recuperação, geração e verificação.

- [ ] **CORS liberado para o frontend**
  - *Verificação:* O frontend em `localhost` chama a API pelo navegador sem erro de CORS.

- [x] **Health é honesto**
  - *Verificação:* `/api/health` reporta falha quando o banco está fora, em vez de responder OK.
