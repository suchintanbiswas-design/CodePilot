import os
from unittest.mock import patch
from app.config.settings import Settings

def test_settings_fallback_database_url():
    settings = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_HOST="testhost",
        POSTGRES_PORT=1234,
        POSTGRES_DB="testdb",
        DATABASE_URL=None, # explicitly not provided
    )
    assert settings.DATABASE_URL == "postgresql+asyncpg://testuser:testpassword@testhost:1234/testdb"

def test_settings_explicit_database_url_takes_precedence():
    settings = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_HOST="testhost",
        POSTGRES_PORT=1234,
        POSTGRES_DB="testdb",
        DATABASE_URL="postgresql+asyncpg://override:pass@otherhost:5432/override_db",
    )
    assert settings.DATABASE_URL == "postgresql+asyncpg://override:pass@otherhost:5432/override_db"

def test_alembic_uses_resolved_url():
    with open("alembic/env.py") as f:
        content = f.read()
        assert "url = settings.DATABASE_URL" in content
        assert "create_async_engine(\n        settings.DATABASE_URL," in content or "create_async_engine(settings.DATABASE_URL" in content

