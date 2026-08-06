# SPEC-FEAT-001 — Critérios de aceite

**Feature:** Base do projeto e identidade visual  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Build limpo**
  - *Verificação:* `npm run build` termina sem erro e sem aviso de TypeScript.

- [x] **Contrato de API tipado ponta a ponta**
  - *Verificação:* Nenhum `any` no cliente de API; alterar um campo do backend quebra a compilação no frontend.

- [x] **Estado do sistema visível**
  - *Verificação:* O cabeçalho mostra o resultado de `/api/health`; com a API fora, exibe estado degradado em vez de tela quebrada.

- [x] **Erro de rede não quebra a tela**
  - *Verificação:* Com a API indisponível, cada painel mostra estado de erro com opção de nova tentativa.

- [ ] **Legibilidade verificada**
  - *Verificação:* Contraste do texto principal atende AA; números usam fonte tabular e não dançam ao atualizar.

- [x] **Chave interna não vaza para o navegador**
  - *Verificação:* Buscar por `INTERNAL_API_KEY` no bundle gerado e no painel de rede do navegador não encontra o valor.

- [ ] **Sobe e desce sem afetar o backend**
  - *Verificação:* `docker compose -f frontend/docker-compose.yml down && up -d` não reinicia os containers de banco e API.
