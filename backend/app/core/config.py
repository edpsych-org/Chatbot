"""
Configuration Settings
Loads from .env file
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Dict, Any
from urllib.parse import urlparse
import os


_SECRET_FIELDS = {
    "SECRET_KEY",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "BREVO_API_KEY",
    "SMTP_PASSWORD",
}


def _mask(v: Any) -> str:
    s = "" if v is None else str(v)
    if not s:
        return "<unset>"
    if len(s) <= 8:
        return "****"
    return f"{s[:4]}…{s[-4:]} (len={len(s)})"


class Settings(BaseSettings):

    # ==================== DATABASE ====================
    DATABASE_URL: str

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, v: str) -> str:
        if not v or not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Invalid DATABASE_URL")
        return v

    @property
    def database_host(self) -> str:
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

    # ==================== AWS ====================
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "eu-west-2"
    S3_BUCKET_IQ_TESTS: str = ""
    S3_BUCKET_REPORTS: str = ""
    S3_BUCKET_TEMP: str = ""
    S3_ENDPOINT_URL: str = ""

    # ==================== LLM ====================
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    USE_GROQ: bool = False

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    USE_OPENAI: bool = False

    # ==================== OCR ====================
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    TESSERACT_LANG: str = "eng"

    # ==================== BACKEND ====================
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_RELOAD: bool = False
    DEBUG_MODE: bool = False
    LOG_LEVEL: str = "INFO"

    # ==================== AUTH ====================
    SECRET_KEY: str

    @field_validator("SECRET_KEY")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("Invalid SECRET_KEY")
        return v

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    MAGIC_LINK_EXPIRY_HOURS: int = 168  # 7 days — invitation links sent Mon often opened on weekend

    # ==================== CORS ====================
    CORS_ORIGINS: str

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _validate_cors(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("CORS_ORIGINS is required")
        return v

    # FIXED VERSION (IMPORTANT)
    @property
    def cors_origins_list(self) -> List[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    # ==================== FILE ====================
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "pdf,png,jpg,jpeg"

    @property
    def allowed_file_types_list(self) -> List[str]:
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]

    # ==================== AI ====================
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 2000
    AI_RETRY_ATTEMPTS: int = 3

    # ==================== REPORT ====================
    REPORT_LANGUAGE: str = "en-GB"
    REPORT_FONT_SIZE: int = 11
    REPORT_PAGE_SIZE: str = "A4"

    # ==================== EMAIL ====================
    BREVO_API_KEY: str = ""
    EMAIL_FROM_NAME: str = "The Ed Psych Practice"
    EMAIL_FROM_ADDRESS: str = "noreply@theedpsych.com"

    # ==================== FRONTEND ====================
    FRONTEND_URL: str

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True

    def safe_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        for k in list(data.keys()):
            if k in _SECRET_FIELDS:
                data[k] = _mask(data[k])
        return data

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
