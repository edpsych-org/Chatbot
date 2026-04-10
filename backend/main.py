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
from app.api import auth, students, chatbot, assignments, student_guardians, hybrid_chat, psychologist, psychologist_reports
from app.models import user, student, assessment, report, assignment, student_guardian, chat, magic_link, verification_token, upload, psychologist_report  # Import all models

# Optional imports - these may fail in chatbot-only deployment
try:
    from app.api import uploads, reports, admin
    HAS_FULL_PIPELINE = True
except ImportError:
    HAS_FULL_PIPELINE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting EdPsych AI Backend...")
    logger.info(f"📊 Database: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}")
    if getattr(settings, 'USE_OPENAI', False):
        logger.info(f"🧠 LLM: OpenAI ({settings.OPENAI_MODEL})")
    elif getattr(settings, 'USE_GROQ', False):
        logger.info(f"🧠 LLM: Groq ({settings.GROQ_MODEL})")
    else:
        logger.info(f"🧠 LLM: {settings.OLLAMA_MODEL} @ {settings.OLLAMA_BASE_URL}")

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


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
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
    llm_status = "openai" if getattr(settings, 'USE_OPENAI', False) else ("groq" if getattr(settings, 'USE_GROQ', False) else ("ollama" if settings.USE_LOCAL_LLM else "disabled"))
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_RELOAD
    )

# Trigger reload - Verification API added


