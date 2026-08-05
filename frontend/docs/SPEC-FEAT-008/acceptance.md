# SPEC-FEAT-008 — Critérios de aceite

**Feature:** Estado de falha não documentada  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Recusa não parece falha do sistema**
  - *Verificação:* O estado usa tratamento visual informativo, distinto do estado de erro da aplicação.

- [ ] **Texto fiel ao enunciado**
  - *Verificação:* A mensagem informa que não há documentação para o problema identificado e sugere registrar um novo documento.

- [ ] **Evidência continua sendo entregue**
  - *Verificação:* Família, contagem de eventos similares e distribuição temporal permanecem visíveis na recusa.

- [ ] **Três causas, três mensagens**
  - *Verificação:* `no_document`, `out_of_distribution` e `state_not_problem` produzem textos e ícones diferentes.

- [ ] **Ciclo fecha na interface**
  - *Verificação:* A partir da recusa, o usuário registra o documento e, ao refazer a análise, recebe a prescrição citada.

- [ ] **Nenhum conselho sem fonte**
  - *Verificação:* Nenhum texto de orientação técnica aparece na tela de recusa.
