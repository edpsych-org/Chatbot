"""
Configuration Settings
Loads from .env file
"""

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
from urllib.parse import urlparse
import os


# Resolve the project root's .env absolutely so the loader works no matter
# which directory the app is launched from.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = str(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    # ==================== DATABASE ====================
    # Single source of truth — matches every managed Postgres on AWS, Neon,
    # Supabase, etc. No default: startup must fail loudly if missing.
    DATABASE_URL: str

    @property
    def database_host(self) -> str:
        """Host parsed from DATABASE_URL — used for the startup log line only."""
        try:
            return urlparse(self.DATABASE_URL).hostname or "unknown"
        except Exception:
            return "unknown"

    @property
    def database_port(self) -> int:
        try:
            return urlparse(self.DATABASE_URL).port or 5432
        except Exception:
            return 5432

    # ==================== AWS S3 (object storage) ====================
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "eu-west-2"
    S3_BUCKET_IQ_TESTS: str = ""
    S3_BUCKET_REPORTS: str = ""
    S3_BUCKET_TEMP: str = ""
    # Optional — leave blank for default AWS; set only for custom / VPC endpoints.
    S3_ENDPOINT_URL: str = ""

    # ==================== GROQ (Cloud LLM) ====================
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    USE_GROQ: bool = False

    # ==================== OPENAI (Cloud LLM) ====================
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    USE_OPENAI: bool = False

    # ==================== TESSERACT OCR ====================
    TESSERACT_PATH: str = "C:/Program Files/Tesseract-OCR/tesseract.exe"
    TESSERACT_LANG: str = "eng"

    # ==================== BACKEND ====================
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_RELOAD: bool = False
    DEBUG_MODE: bool = False
    LOG_LEVEL: str = "INFO"

    # ==================== JWT AUTHENTICATION ====================
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    MAGIC_LINK_EXPIRY_HOURS: int = 48

    # ==================== CORS ====================
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:3002,http://127.0.0.1:3002"

    # ==================== FILE UPLOAD ====================
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "pdf,png,jpg,jpeg"

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert ALLOWED_FILE_TYPES string to list"""
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]

    # ==================== AI GENERATION ====================
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 2000
    AI_RETRY_ATTEMPTS: int = 3

    # ==================== REPORT GENERATION ====================
    REPORT_LANGUAGE: str = "en-GB"
    REPORT_FONT_SIZE: int = 11
    REPORT_PAGE_SIZE: str = "A4"

    # ==================== EMAIL ====================
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@edpsych.com"
    FRONTEND_URL: str = "http://localhost:3002"

    class Config:
        env_file = _ENV_FILE
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env (like frontend vars)


# Initialize settings
settings = Settings()
