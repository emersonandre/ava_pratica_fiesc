# executar aplicação backend app/main.py
uvicorn app.main:app

# CLI administrativa (injeta dados no banco para teste)
python manage.py ingest