# SPEC-FEAT-001 — Critérios de aceite

**Feature:** Infraestrutura local reproduzível  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **O compose do backend deixa o banco pronto**
  - *Verificação:* Após `docker compose -f backend/docker-compose.yml up -d`, `SELECT extversion FROM pg_extension WHERE extname='vector'` retorna uma versão.

- [x] **Frontend e backend sobem de forma independente**
  - *Verificação:* Derrubar e subir o compose do frontend não reinicia o container do banco nem o da API.

- [x] **Inicialização é idempotente**
  - *Verificação:* Rodar `init_db` duas vezes seguidas termina com código 0 e sem exceção nas duas execuções.

- [x] **Nenhum segredo versionado**
  - *Verificação:* `.env` está no `.gitignore`; cada app tem `.env.example` com todas as chaves e valores de exemplo.

- [x] **Configuração falha cedo e com clareza**
  - *Verificação:* Subir a API sem `LLM_API_KEY` produz erro de validação nomeando a variável ausente, não um erro em tempo de requisição.

- [x] **Porta não conflita com Postgres local**
  - *Verificação:* O compose expõe 5433 no host para não colidir com uma instalação existente na 5432.
