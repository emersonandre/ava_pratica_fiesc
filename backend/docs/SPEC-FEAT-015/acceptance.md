# SPEC-FEAT-015 — Critérios de aceite

**Feature:** Testes, qualidade e observabilidade  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Suíte roda em um comando e passa**
  - *Verificação:* `pytest -q` termina com todos os testes verdes na máquina limpa.

- [x] **Lint sem pendências**
  - *Verificação:* `ruff check .` e `ruff format --check .` terminam sem erro.

- [x] **Regras críticas cobertas**
  - *Verificação:* Existem testes para taxonomia, features, gate de cobertura e casos adversariais de alucinação.

- [x] **Histórico de commits conta a construção**
  - *Verificação:* O `git log` mostra commits incrementais com mensagens no padrão Conventional Commits, não um commit único.

- [x] **Observabilidade real**
  - *Verificação:* Toda requisição registra identificador, rota, tempo por etapa e resultado em log JSON.

- [ ] **README permite reproduzir do zero**
  - *Verificação:* Um leitor sem contexto sobe o ambiente, ingere os dados e executa a demonstração seguindo apenas o README.
