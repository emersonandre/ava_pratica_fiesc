# SPEC-FEAT-005 — Critérios de aceite

**Feature:** Análise de evento e simulador  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **JSON do enunciado funciona**
  - *Verificação:* Colar o exemplo do §2 do desafio e executar produz análise completa.

- [ ] **JSON inválido é explicado**
  - *Verificação:* Campo ausente ou tipo errado gera mensagem apontando o campo, sem chamar a API.

- [ ] **Amostra é sempre de holdout**
  - *Verificação:* Todo evento carregado pelo botão tem data entre 10 e 16/jun/2026.

- [ ] **Gabarito visível**
  - *Verificação:* O rótulo real do evento aparece ao lado do diagnóstico, com indicação de acerto ou erro.

- [ ] **Fora de distribuição é comunicado**
  - *Verificação:* Evento fora de distribuição exibe aviso específico, distinto de "falha sem documento".

- [ ] **Desempenho transparente**
  - *Verificação:* Os tempos por etapa aparecem na interface após a análise.
