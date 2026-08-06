# Imagem da API.
#
# `slim` em vez de `alpine`: numpy, scikit-learn e onnxruntime distribuem rodas
# pre-compiladas para glibc. No Alpine (musl) o pip cairia em compilacao a
# partir do fonte -- build de dezenas de minutos e imagem maior no fim.

FROM python:3.13-slim

# Nao rodar como root: o container so precisa ler codigo e escrever em artifacts.
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/backend

# Dependencias antes do codigo: aproveita o cache de camada entre builds.
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend

# O modelo de embeddings e o de OCR sao baixados na primeira execucao e ficam
# em artifacts/, que e volume. Mantem a imagem enxuta e permite trocar o modelo
# sem reconstruir.
RUN mkdir -p /app/backend/artifacts && chown -R app:app /app

USER app
WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/health', timeout=4).status < 500 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
