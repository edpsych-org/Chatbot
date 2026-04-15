"""
Centralised logging setup.

Two-tier strategy:
- Console (stdout) handler stays — Docker/CloudWatch/Vercel capture it.
- Rotating file handlers write app.log (everything) and errors.log (ERROR+)
  into backend/logs/ for local debugging.
"""

from __future__ import annotations

import logging
import logging.config
import os
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str | None = None) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    resolved = (level or os.getenv("LOG_LEVEL") or "INFO").upper()

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": LOG_FORMAT, "datefmt": DATE_FORMAT},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": resolved,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "app_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": resolved,
                "formatter": "standard",
                "filename": str(LOG_DIR / "app.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "standard",
                "filename": str(LOG_DIR / "errors.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["console", "app_file", "error_file"], "level": resolved, "propagate": False},
            "uvicorn.error": {"handlers": ["console", "app_file", "error_file"], "level": resolved, "propagate": False},
            "uvicorn.access": {"handlers": ["console", "app_file"], "level": "INFO", "propagate": False},
            "sqlalchemy.engine": {"handlers": ["console", "app_file"], "level": "WARNING", "propagate": False},
        },
        "root": {
            "handlers": ["console", "app_file", "error_file"],
            "level": resolved,
        },
    }

    logging.config.dictConfig(config)
    logging.getLogger(__name__).debug("Logging configured (level=%s, dir=%s)", resolved, LOG_DIR)
