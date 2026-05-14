"""
Pytest configuration: inject stub env vars before any app module is imported.
These values are fake — tests never touch a real database or external service.
"""
import os

# Satisfy the four required Settings fields so app.core.config loads cleanly.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-xx")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
