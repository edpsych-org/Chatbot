"""
Configuration Settings
Loads from .env file
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Dict, Any
from urllib.parse import urlparse


# Fields whose values must never appear in logs or the /health banner.
# safe_dict() replaces these with masked placeholders.
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


def _normalize_origin(value: str) -> str:
    """Return a clean origin string for stable CORS matching."""
    origin = value.strip().strip("\"'")
    if origin.startswith("CORS_ORIGINS="):
        origin = origin.split("=", 1)[1].strip()
    if origin.endswith("/"):
        origin = origin.rstrip("/")
    return origin


def _parse_cors_origins(value: str) -> List[str]:
    """Parse comma/newline separated origins and normalize common mistakes."""
    origins: List[str] = []
    seen: set[str] = set()
    for chunk in value.replace("\n", ",").split(","):
        origin = _normalize_origin(chunk)
        if not origin or origin in seen:
            continue
        seen.add(origin)
        origins.append(origin)
    return origins


class Settings(BaseSettings):
    # ==================== DATABASE ====================
    # Single source of truth — matches every managed Postgres on AWS, Neon,
    # Supabase, etc. No default: startup must fail loudly if missing.
    DATABASE_URL: str

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, v: str) -> str:
        if not v or not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql://' or "
                "'postgresql+asyncpg://'. Got: "
                + (v[:40] + "…" if len(v) > 40 else v or "<empty>")
            )
        return v

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
    # Linux container default. Override on Windows dev:
    #   TESSERACT_PATH=C:/Program Files/Tesseract-OCR/tesseract.exe
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    TESSERACT_LANG: str = "eng"

    # ==================== BACKEND ====================
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_RELOAD: bool = False
    DEBUG_MODE: bool = False
    LOG_LEVEL: str = "INFO"

    # ==================== JWT AUTHENTICATION ====================
    # Required — startup fails if missing. Generate per env:
    #   python -c "import secrets; print(secrets.token_urlsafe(48))"
    SECRET_KEY: str

    @field_validator("SECRET_KEY")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError("SECRET_KEY is required and must not be empty.")
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 chars (got {len(v)}). "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if "change-this" in v.lower() or "your-super-secret" in v.lower():
            raise ValueError(
                "SECRET_KEY is still the placeholder value. Replace it with "
                "a generated secret before starting the app."
            )
        return v

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    MAGIC_LINK_EXPIRY_HOURS: int = 48

    # ==================== CORS ====================
    # Required — comma-separated allowed origins. Must include the deployed
    # frontend URL in production.
    CORS_ORIGINS: str

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _validate_cors(cls, v: str) -> str:
        origins = _parse_cors_origins(v)
        if not origins:
            raise ValueError(
                "CORS_ORIGINS is required (comma-separated origins, e.g. "
                "'http://localhost:3000,https://app.theedpsych.com')."
            )
        return ",".join(origins)

    # ==================== FILE UPLOAD ====================
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "pdf,png,jpg,jpeg"

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return _parse_cors_origins(self.CORS_ORIGINS)

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

    # ==================== EMAIL (Brevo transactional API) ====================
    BREVO_API_KEY: str = ""  # blank in dev → emails log to backend/logs/app.log
    EMAIL_FROM_NAME: str = "The Ed Psych Practice"
    EMAIL_FROM_ADDRESS: str = "noreply@theedpsych.com"

    # ==================== FRONTEND URL ====================
    # Required — used in magic-link emails and CORS. No default so a missing
    # value can't silently send people to the wrong place in production.
    FRONTEND_URL: str

    # ==================== EMAIL — DEPRECATED SMTP FALLBACK ====================
    # Kept only because legacy assignments.py + student_guardians.py still
    # reference these. Brevo is the active path; leave SMTP_* unset.
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True

    def safe_dict(self) -> Dict[str, Any]:
        """Return settings as a dict with every secret masked.

        Use this for startup banners, debug endpoints, and support dumps —
        never log `settings.dict()` directly, it includes every secret.
        """
        data = self.model_dump()
        for k in list(data.keys()):
            if k in _SECRET_FIELDS:
                data[k] = _mask(data[k])
        return data

    class Config:
        # Relative to current working directory.
        # - In Docker:  the WORKDIR is /app, so /app/.env (mounted via compose
        #               or env vars injected via env_file:) is used.
        # - Locally:    run the backend from the project root so .env resolves
        #               there, OR copy .env into backend/, OR export the vars
        #               in your shell.
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env (like frontend vars)


# Initialize settings
settings = Settings()
