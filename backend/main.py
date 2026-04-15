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
from app.models import user, student, assessment, report, assignment, student_guardian, chat, magic_link, upload, psychologist_report  # Import all models

# Optional imports - these may fail in chatbot-only deployment
try:
    from app.api import uploads, reports, admin
    HAS_FULL_PIPELINE = True
except ImportError:
    HAS_FULL_PIPELINE = False

# Configure logging (file + stdout, rotating files in backend/logs/)
setup_logging(getattr(settings, "LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
http_logger = logging.getLogger("http")


def _log_loaded_config() -> None:
    """Emit the banner + a masked dump of every setting at INFO level."""
    logger.info("🚀 Starting EdPsych AI Backend...")
    logger.info("📊 Database: %s:%s", settings.database_host, settings.database_port)
    if getattr(settings, "USE_OPENAI", False):
        logger.info("🧠 LLM: OpenAI (%s)", settings.OPENAI_MODEL)
    elif getattr(settings, "USE_GROQ", False):
        logger.info("🧠 LLM: Groq (%s)", settings.GROQ_MODEL)
    else:
        logger.info("🧠 LLM: disabled (no provider enabled — set USE_OPENAI or USE_GROQ)")

    safe = settings.safe_dict()
    for key in sorted(safe):
        logger.info("  %s = %s", key, safe[key])


def _validate_runtime_config() -> None:
    """Log loud warnings for remaining runtime-level inconsistencies.

    Schema validation (required fields, SECRET_KEY length, URL shape) now
    happens in Settings field_validators, so startup already fails loudly
    on those. This only catches cross-field issues.
    """
    if getattr(settings, "USE_OPENAI", False) and not settings.OPENAI_API_KEY:
        logger.error("USE_OPENAI=true but OPENAI_API_KEY is empty — chat/report calls will fail.")
    if getattr(settings, "USE_GROQ", False) and not settings.GROQ_API_KEY:
        logger.error("USE_GROQ=true but GROQ_API_KEY is empty — chat acknowledgements will fail.")


async def _wait_for_db(max_attempts: int = 8, base_delay: float = 1.0) -> None:
    """Block startup until the database accepts a connection.

    Uses exponential backoff (1, 2, 4, 8, … capped at 30 seconds between
    attempts). Raises the last exception if the DB never becomes ready.
    Fixes the compose race where backend starts before postgres is
    accepting TCP, and is the same pattern you want on AWS RDS when the
    cluster is still warming up.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database reachable at %s:%s", settings.database_host, settings.database_port)
            return
        except Exception as exc:  # noqa: BLE001 — any connection failure is retryable here
            last_exc = exc
            delay = min(base_delay * (2 ** (attempt - 1)), 30.0)
            logger.warning(
                "⏳ Database not ready (attempt %s/%s): %s — retry in %.1fs",
                attempt, max_attempts, exc.__class__.__name__, delay,
            )
            if attempt < max_attempts:
                await asyncio.sleep(delay)

    logger.error("❌ Database still unreachable after %s attempts.", max_attempts)
    raise last_exc  # type: ignore[misc]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    _log_loaded_config()
    _validate_runtime_config()

    # Wait for Postgres to accept connections before touching the schema.
    await _wait_for_db()

    # Create / verify database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created/verified")

    yield

    # Shutdown
    logger.info("👋 Shutting down EdPsych AI Backend...")


# Initialize FastAPI app
app = FastAPI(
    title="EdPsych AI API",
    description="Production-level Educational Psychology AI Report Generation System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing + access-log middleware
_SKIP_LOG_PATHS = {"/health", "/api/docs", "/api/redoc", "/openapi.json", "/api/openapi.json"}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    elapsed_ms = int((time.time() - start_time) * 1000)
    response.headers["X-Process-Time"] = f"{elapsed_ms}ms"

    path = request.url.path
    if path not in _SKIP_LOG_PATHS:
        client = request.client.host if request.client else "-"
        status = response.status_code
        line = f"{status} {request.method} {path} {elapsed_ms}ms client={client}"
        if status >= 500:
            http_logger.error(line)
        elif status >= 400:
            http_logger.warning(line)
        else:
            http_logger.info(line)
    return response


# Global exception handler
# Must include CORS headers so the browser can read the error instead of
# reporting a misleading "CORS blocked" message.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    origin = request.headers.get("origin", "")
    headers = {}
    if origin and origin in settings.cors_origins_list:
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


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "EdPsych AI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    if getattr(settings, 'USE_OPENAI', False):
        llm_status = "openai"
    elif getattr(settings, 'USE_GROQ', False):
        llm_status = "groq"
    else:
        llm_status = "disabled"
    return {
        "status": "healthy",
        "database": "connected",
        "llm": llm_status,
        "timestamp": time.time()
    }


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Students"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["Chatbot"])
if HAS_FULL_PIPELINE:
    app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["File Uploads"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(assignments.router, prefix="/api/v1", tags=["Assignments"])
app.include_router(student_guardians.router, prefix="/api/v1", tags=["Student-Guardians"])
app.include_router(hybrid_chat.router, prefix="/api/v1", tags=["Hybrid Chat"])
app.include_router(psychologist.router, prefix="/api/v1", tags=["Psychologist"])
app.include_router(psychologist_reports.router, prefix="/api/v1", tags=["Psychologist Reports"])
app.include_router(client_errors.router, prefix="/api/v1", tags=["Client Errors"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_RELOAD
    )

# Trigger reload - Verification API added


