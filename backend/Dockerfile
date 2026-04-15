# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ---- System deps ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libpq5 \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---- App setup ----
WORKDIR /app

# ✅ Copy requirements first (cache optimization)
COPY requirements-deploy.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copy .env file into container
#COPY .env .env

# ✅ Copy rest of app
COPY . .

# ---- Build-time check ----
ENV DATABASE_URL=postgresql+asyncpg://build:build@localhost:5432/build

RUN python -m compileall -q app main.py \
    && python -c "import boto3, fastapi, sqlalchemy, asyncpg, jose, passlib, pydantic_settings, httpx, requests, aiohttp, fitz, pdf2image, pytesseract, PIL; print('deps import OK')" \
    && python -c "import main; print('main import OK')"

# ❗ DO NOT clear DATABASE_URL now (we rely on .env)
# ENV DATABASE_URL=

# ---- Runtime user ----
RUN useradd --system --uid 1001 --home-dir /app --shell /usr/sbin/nologin edpsych \
    && mkdir -p /app/logs \
    && chown -R edpsych:edpsych /app

USER edpsych

# ---- Network ----
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, sys; \
    sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else sys.exit(1)"

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]