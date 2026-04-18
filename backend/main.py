"""
EdPsych AI - Main FastAPI Application
Production-level prototype with local LLM integration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import asyncio
import time
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging
from app.api import auth, students, chatbot, assignments, student_guardians, hybrid_chat, psychologist, psychologist_reports, client_errors
from app.models import user, student, assessment, report, assignment, student_guardian, chat, magic_link, upload, psychologist_report

try:
    from app.api import uploads, reports, admin
    HAS_FULL_PIPELINE = True
except ImportError:
    HAS_FULL_PIPELINE = False


setup_logging(getattr(settings, "LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
http_logger = logging.getLogger("http")


def _log_loaded_config() -> None:
    logger.info("🚀 Starting EdPsych AI Backend...")
    logger.info("📊 Database: %s:%s", settings.database_host, settings.database_port)

    if getattr(settings, "USE_OPENAI", False):
        logger.info("🧠 LLM: OpenAI (%s)", settings.OPENAI_MODEL)
    elif getattr(settings, "USE_GROQ", False):
        logger.info("🧠 LLM: Groq (%s)", settings.GROQ_MODEL)
    else:
        logger.info("🧠 LLM: disabled")

    safe = settings.safe_dict()
    for key in sorted(safe):
        logger.info("  %s = %s", key, safe[key])


def _validate_runtime_config() -> None:
    if getattr(settings, "USE_OPENAI", False) and not settings.OPENAI_API_KEY:
        logger.error("OPENAI enabled but key missing")
    if getattr(settings, "USE_GROQ", False) and not settings.GROQ_API_KEY:
        logger.error("GROQ enabled but key missing")


async def _wait_for_db(max_attempts: int = 8, base_delay: float = 1.0) -> None:
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connected")
            return
        except Exception as exc:
            last_exc = exc
            delay = min(base_delay * (2 ** (attempt - 1)), 30.0)
            logger.warning(f"DB not ready (attempt {attempt}): retry in {delay}s")
            if attempt < max_attempts:
                await asyncio.sleep(delay)

    raise last_exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log_loaded_config()
    _validate_runtime_config()

    await _wait_for_db()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ DB ready")
    yield
    logger.info("👋 Shutdown")


app = FastAPI(
    title="EdPsych AI API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS Middleware (unchanged)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SKIP_LOG_PATHS = {"/health", "/api/docs", "/api/redoc", "/openapi.json", "/api/openapi.json"}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)

    elapsed_ms = int((time.time() - start_time) * 1000)
    response.headers["X-Process-Time"] = f"{elapsed_ms}ms"

    if request.url.path not in _SKIP_LOG_PATHS:
        status = response.status_code
        line = f"{status} {request.method} {request.url.path} {elapsed_ms}ms"
        if status >= 500:
            http_logger.error(line)
        elif status >= 400:
            http_logger.warning(line)
        else:
            http_logger.info(line)

    return response


# FIXED GLOBAL EXCEPTION HANDLER (CORS SAFE)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)

    origin = request.headers.get("origin", "")
    headers = {}

    # NORMALIZE origin (THIS FIXES YOUR ISSUE)
    normalized_origin = origin.rstrip("/") if origin else ""

    if normalized_origin and normalized_origin in settings.cors_origins_list:
        headers["access-control-allow-origin"] = origin
        headers["access-control-allow-credentials"] = "true"

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG_MODE else "An error occurred"
        },
        headers=headers,
    )


@app.get("/")
async def root():
    return {"status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "time": time.time()}


# Routers
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(students.router, prefix="/api/v1/students")
app.include_router(chatbot.router, prefix="/api/v1/chatbot")

if HAS_FULL_PIPELINE:
    app.include_router(uploads.router, prefix="/api/v1/uploads")
    app.include_router(reports.router, prefix="/api/v1/reports")
    app.include_router(admin.router, prefix="/api/v1/admin")

app.include_router(assignments.router, prefix="/api/v1")
app.include_router(student_guardians.router, prefix="/api/v1")
app.include_router(hybrid_chat.router, prefix="/api/v1")
app.include_router(psychologist.router, prefix="/api/v1")
app.include_router(psychologist_reports.router, prefix="/api/v1")
app.include_router(client_errors.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_RELOAD
    )
