# SPEC-FEAT-012 — Critérios de aceite

**Feature:** Guarda anti-alucinação  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Falha coberta é respondida com citação**
  - *Verificação:* Pergunta sobre desalinhamento retorna prescrição citando o Doc2.

- [x] **Falha sem documento é recusada**
  - *Verificação:* Pergunta sobre família descoberta retorna a recusa do enunciado e nenhuma chamada de LLM no log.

- [x] **Pergunta fora de domínio é recusada**
  - *Verificação:* "Qual a capital da França?" recebe recusa educada, sem tentativa de resposta.

- [x] **Premissa falsa não é aceita**
  - *Verificação:* Pergunta que afirma um procedimento inexistente ("conforme a seção 9 do manual de correias, ...") recebe correção em vez de confirmação.

- [x] **Afirmação sem embasamento é removida**
  - *Verificação:* Em caso injetado com afirmação não sustentada pelo contexto, ela não aparece na resposta final e consta em `removed`.

- [x] **Embasamento é medido**
  - *Verificação:* Toda resposta traz `GroundingReport`; o score médio da suíte adversarial está no README.

- [x] **Suíte roda em um comando**
  - *Verificação:* `pytest tests/test_alucinacao.py` executa todos os casos e passa.
