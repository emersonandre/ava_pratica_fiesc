# Comandos

Todos rodam a partir de `backend/`, com a venv ativa.

## Primeira execução

```powershell
# 1. Segredos de autenticação (a API nao sobe sem eles -- por desenho)
python manage.py secrets
# cole a saida em backend/.env; a INTERNAL_API_KEY vai tambem em frontend/.env

# 2. Banco (container Docker local, porta 5433)
docker network create prescritiva-net
docker compose up -d db

# 3. Schema e dados
python manage.py initdb
python manage.py ingest        # ~167 mil registros, alguns minutos
```

## Dia a dia

```powershell
python manage.py check                 # banco, dados, scaler, LLM, segredos
python manage.py runserver --reload    # http://127.0.0.1:8001/docs
python manage.py report                # relatorios em docs/analise/
python manage.py shell                 # REPL com session e modelos
pytest -q
ruff check . && ruff format .
```

## Executar a aplicação ASGI direto

`manage.py runserver` e um atalho para o uvicorn. O equivalente explicito:

```powershell
uvicorn app.main:app --port 8001 --reload
```

> **Porta 8001, nao 8000.** A 8000 costuma estar ocupada por outro projeto Python na
> maquina. Mesmo motivo da 5433 no PostgreSQL. Se a porta estiver em uso, o uvicorn
> falha com `[Errno 10048]` e qualquer resposta em `localhost:8000` vem do outro servico.

## Banco

```powershell
docker compose ps                      # estado do container
docker compose logs -f db
docker compose down                    # para (mantem o volume)
docker compose down -v                 # para e APAGA os dados
python manage.py initdb --drop         # recria o schema do zero
```

## Erros comuns

| Sintoma | Causa | Solucao |
| --- | --- | --- |
| `RuntimeError: Variaveis de autenticacao ausentes` | `.env` sem os segredos | `python manage.py secrets` e preencher `backend/.env` |
| `[Errno 10048] error while attempting to bind` | Porta ja em uso | Usar `--port 8001` ou liberar a porta |
| `scaler.joblib nao encontrado` | Ingestao nao rodou | `python manage.py ingest` |
| `sem conexao com o PostgreSQL` | Container parado | `docker compose up -d db` |
