# syntax=docker/dockerfile:1.6
# ---- EdPsych Backend ---------------------------------------------------
# Python 3.11 slim + OCR deps. Runs Uvicorn as a non-root user on :8000.
# Logs stream to stdout so Docker / CloudWatch capture them automatically.

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ---- System deps (OCR + Postgres client libs + tini for PID 1) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        libpq5 \
        tini \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
WORKDIR /app
COPY requirements-deploy.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---- App source ----
COPY . .

# ---- Build-time smoke check ----
# Fail the build (not runtime) if any third-party dep is missing from
# requirements.txt. Bytecode-compile everything and directly import the
# heavy externals that the app relies on. We set a dummy DATABASE_URL so
# pydantic-settings doesn't reject the validation at import time.
ENV DATABASE_URL=postgresql+asyncpg://build:build@localhost:5432/build
RUN python -m compileall -q app main.py \
    && python -c "import boto3, fastapi, sqlalchemy, asyncpg, jose, passlib, pydantic_settings, httpx, requests, aiohttp, fitz, pdf2image, pytesseract, PIL; print('deps import OK')" \
    && python -c "import main; print('main import OK')"
ENV DATABASE_URL=

# ---- Runtime user ----
RUN useradd --system --uid 1001 --home-dir /app --shell /usr/sbin/nologin edpsych \
    && mkdir -p /app/logs \
    && chown -R edpsych:edpsych /app
USER edpsych

# ---- Network + healthcheck ----
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, sys; \
sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else sys.exit(1)"

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
