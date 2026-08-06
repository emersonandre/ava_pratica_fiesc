# SPEC-FEAT-008 — Critérios de aceite

**Feature:** Mapa falha→documento e gate de cobertura  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Gate roda antes do LLM**
  - *Verificação:* Com família sem cobertura, o log da requisição não registra nenhuma chamada ao provider de LLM.

- [x] **Recusa segue o texto do enunciado**
  - *Verificação:* A resposta informa que não há documento para o problema identificado e sugere registrar um novo documento.

- [x] **Recusa ainda entrega valor**
  - *Verificação:* O payload de recusa traz a família diagnosticada, a contagem de eventos similares e a distribuição temporal.

- [x] **Estado não vira prescrição**
  - *Verificação:* Evento diagnosticado como `normal` ou `motor_desligado` retorna `reason = state_not_problem`, sem prescrição.

- [ ] **Fora de distribuição é distinguido de falta de documento**
  - *Verificação:* Evento fora de distribuição retorna `reason = out_of_distribution`, com mensagem diferente da de documento ausente.

- [x] **Cobertura se atualiza sozinha**
  - *Verificação:* Após upload de documento para uma família descoberta, `check_coverage` passa a retornar `is_covered = True` sem reiniciar a API.

- [x] **Mapa é auditável**
  - *Verificação:* `backend/docs/analise/cobertura.md` lista cada família, o documento vinculado e a evidência que sustentou o vínculo.
