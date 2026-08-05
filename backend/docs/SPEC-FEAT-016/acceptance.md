# SPEC-FEAT-016 — Critérios de aceite

**Feature:** Autenticação: JWT externo e chave interna  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Endpoint externo sem token é recusado**
  - *Verificação:* `POST /api/v1/predict` sem `Authorization` retorna 401 com mensagem indicando o cabeçalho esperado.

- [ ] **Token válido é aceito**
  - *Verificação:* Token obtido em `/api/v1/auth/token` com credencial correta dá acesso a `/api/v1/predict`.

- [ ] **Credencial errada não emite token**
  - *Verificação:* `client_secret` incorreto retorna 401 e nenhum token é gerado.

- [ ] **Escopo é verificado**
  - *Verificação:* Token emitido apenas com escopo `predict` recebe 403 ao chamar `/api/v1/upload_doc`.

- [ ] **Token expirado é rejeitado**
  - *Verificação:* Token com `exp` no passado retorna 401 com mensagem de expiração, distinta da de token inválido.

- [ ] **Assinatura adulterada é rejeitada**
  - *Verificação:* Token assinado com outro segredo retorna 401.

- [ ] **Endpoint interno exige a chave**
  - *Verificação:* `/api/internal/stats/overview` sem `X-Internal-Key` retorna 401; com a chave correta, 200.

- [ ] **Segredos não vazam**
  - *Verificação:* Nenhum segredo aparece em log, em resposta de erro ou no bundle do frontend.

- [ ] **API não sobe sem segredo**
  - *Verificação:* Iniciar a aplicação com `JWT_SECRET` vazio falha na inicialização nomeando as variáveis ausentes.
