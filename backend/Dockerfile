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

# ---- Install Python deps (cached layer — only re-runs when requirements change)
COPY requirements-deploy.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy app source ----
# NOTE: .env is deliberately NOT copied into the image — see .dockerignore.
# Real values come from one of these at runtime, in order of preference:
#   1. docker-compose `env_file: .env` (local dev)
#   2. ECS task-definition env vars sourced from AWS Secrets Manager / SSM (prod)
#   3. `docker run -e VAR=...` or `--env-file` on the CLI
# Baking .env into the image would freeze secrets into every published layer.
COPY . .

# ---- Build-time check (safe dummy envs) ----
RUN set -e; \
    export DATABASE_URL=postgresql+asyncpg://build:build@localhost:5432/build; \
    export SECRET_KEY=build-time-only-do-not-use-in-production-min-32-chars; \
    export CORS_ORIGINS=http://localhost:3000; \
    export FRONTEND_URL=http://localhost:3000; \
    python -m compileall -q app main.py; \
    python -c "import main; print('main import OK')"

# ---- Runtime user ----
RUN useradd --system --uid 1001 --home-dir /app --shell /usr/sbin/nologin edpsych \
    && mkdir -p /app/logs \
    && chown -R edpsych:edpsych /app

USER edpsych

# ---- Network ----
EXPOSE 8000

# ---- Healthcheck ----
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, sys; \
    sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else sys.exit(1)"

# ---- Start ----
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]