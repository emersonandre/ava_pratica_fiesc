# SPEC-FEAT-011 — Critérios de aceite

**Feature:** Geração prescritiva com citações  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Todo passo é citado**
  - *Verificação:* Nenhum item de `inspecao`, `correcao` ou `validacao` fica sem ao menos uma citação.

- [x] **Citações são verificáveis**
  - *Verificação:* Cada citação aponta para um documento e página existentes; o trecho correspondente é recuperável.

- [x] **Números não vêm do modelo**
  - *Verificação:* Os valores de `evidencia` batem exatamente com a resposta de `/api/events/similar` para o mesmo evento.

- [x] **Sem contexto, o modelo não é chamado**
  - *Verificação:* Recuperação vazia resulta em resposta de recusa, sem nenhuma chamada ao provider.

- [x] **Resposta em português técnico**
  - *Verificação:* As respostas usam a terminologia dos manuais (mancal, acoplamento, crest factor), sem mistura de idiomas.

- [x] **Formato sempre válido**
  - *Verificação:* Sobre 20 execuções variadas, o parse do schema não falha; falha de formato dispara uma reexecução e é registrada.
