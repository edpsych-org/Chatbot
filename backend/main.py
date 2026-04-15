"""
EdPsych AI - Main FastAPI Application
Production-level prototype with local LLM integration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
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


def _validate_runtime_config():
    """Log loud warnings for insecure-but-common misconfigurations."""
    if "change-this" in settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        logger.error(
            "SECRET_KEY is using the default placeholder — JWT tokens are NOT secure. "
            "Set a strong SECRET_KEY (32+ random chars) in .env before deploying."
        )
    if getattr(settings, "USE_OPENAI", False) and not settings.OPENAI_API_KEY:
        logger.error("USE_OPENAI=true but OPENAI_API_KEY is empty in .env")
    if getattr(settings, "USE_GROQ", False) and not settings.GROQ_API_KEY:
        logger.error("USE_GROQ=true but GROQ_API_KEY is empty in .env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting EdPsych AI Backend...")
    logger.info(f"📊 Database: {settings.database_host}:{settings.database_port}")
    if getattr(settings, 'USE_OPENAI', False):
        logger.info(f"🧠 LLM: OpenAI ({settings.OPENAI_MODEL})")
    elif getattr(settings, 'USE_GROQ', False):
        logger.info(f"🧠 LLM: Groq ({settings.GROQ_MODEL})")
    else:
        logger.info("🧠 LLM: disabled (no provider enabled — set USE_OPENAI or USE_GROQ)")

    _validate_runtime_config()

    # Create database tables
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


