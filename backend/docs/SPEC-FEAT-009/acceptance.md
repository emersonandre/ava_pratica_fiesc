# SPEC-FEAT-009 — Critérios de aceite

**Feature:** Provider de LLM plugável  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Troca de provider é só configuração**
  - *Verificação:* Alternar `LLM_PROVIDER` entre `openai` e `deepseek` no `.env` muda o provider efetivo sem alterar código de negócio.

- [ ] **Falta de capacidade falha cedo**
  - *Verificação:* Configurar um modelo sem visão e disparar o OCR produz erro na inicialização do pipeline, com mensagem nomeando a capacidade ausente.

- [ ] **Indisponibilidade não derruba a API**
  - *Verificação:* Com credencial inválida, `/api/chat` retorna erro de negócio com mensagem acionável e a API continua respondendo `/api/stats/overview`.

- [ ] **Retry é limitado e observável**
  - *Verificação:* Falha transitória é repetida com backoff até o teto configurado; cada tentativa aparece no log.

- [ ] **Consumo é rastreável**
  - *Verificação:* Cada chamada registra modelo, tokens de entrada/saída e latência em log estruturado.
