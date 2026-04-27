# syntax=docker/dockerfile:1.7
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Europe/Madrid

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY codere_scraper.py http_client.py models.py run.py supabase_persist.py ./

# Cron de Railway usa `startCommand` de railway.json; CMD por defecto por si ejecutas el contenedor a mano.
CMD ["python", "run.py", "--supabase-only"]
