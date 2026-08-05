# SPEC-FEAT-010 — Critérios de aceite

**Feature:** Recuperação de contexto para prescrição  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Nenhum vazamento entre famílias**
  - *Verificação:* Consulta sobre falha de correia retorna apenas trechos do Doc4; nenhum chunk do Doc3 aparece.

- [ ] **Seções acionáveis vêm primeiro em pedido de correção**
  - *Verificação:* Para "como corrigir", os três primeiros trechos pertencem a seções de procedimento/correção.

- [ ] **Orçamento de tokens respeitado sem truncar chunk**
  - *Verificação:* O contexto montado fica dentro do orçamento e nenhum chunk aparece cortado ao meio.

- [ ] **Proveniência completa**
  - *Verificação:* Todo `RetrievedChunk` tem documento e faixa de páginas — pré-requisito da citação.

- [ ] **Família sem cobertura não chega aqui**
  - *Verificação:* Chamar `retrieve` com família descoberta levanta erro; o gate deveria ter interrompido antes.
