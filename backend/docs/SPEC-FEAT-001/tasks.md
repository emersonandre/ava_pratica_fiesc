# SPEC-FEAT-001 — Tarefas

**Feature:** Infraestrutura local reproduzível

- [x] Criar `backend/docker-compose.yml` com serviços `db` e `api`, volume, healthcheck e rede externa
- [x] Criar `frontend/docker-compose.yml` com o serviço `web` na mesma rede externa
- [x] Criar `backend/.env.example` e `frontend/.env.example` com todas as variáveis documentadas
- [x] Implementar `app/config.py` com `Settings` (pydantic-settings) e cache de instância
- [x] Implementar `app/db.py`: engine SQLAlchemy, sessão e verificação de conectividade
- [x] Implementar `app/scripts/init_db.py` (extensão + tabelas + índices, idempotente)
- [x] Implementar `app/scripts/gen_secrets.py` para gerar os segredos de autenticação
- [x] Implementar `manage.py` com os comandos administrativos
- [x] Criar `.gitignore` cobrindo `.venv`, `.env`, `__pycache__`, artefatos de modelo
- [x] Escrever os `Dockerfile` de backend e frontend
- [ ] Validar: subir do zero em máquina limpa e registrar o tempo no README

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
