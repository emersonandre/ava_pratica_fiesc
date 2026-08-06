# SPEC-FEAT-007 — Critérios de aceite

**Feature:** Chat prescritivo com citações  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Prescrição legível por seções**
  - *Verificação:* Diagnóstico, inspeção, correção e validação aparecem separados e na ordem.

- [ ] **Citação abre o trecho real**
  - *Verificação:* Clicar em uma citação exibe o texto do chunk recuperado, com documento e página.

- [x] **Embasamento exposto**
  - *Verificação:* O score de grounding aparece na resposta, junto do que foi removido por falta de suporte.

- [x] **Contexto do evento persiste**
  - *Verificação:* Uma pergunta de acompanhamento ("e como valido depois?") é respondida sem reenviar o evento.

- [x] **Erro do provider é comunicado**
  - *Verificação:* Falha do LLM mostra mensagem acionável e mantém o histórico da conversa.

- [ ] **Interação fluida na demonstração**
  - *Verificação:* A resposta começa a aparecer em poucos segundos (streaming) ou há indicação clara de progresso.
