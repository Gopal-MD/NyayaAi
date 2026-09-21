from app.core.config import settings


def test_database_url_uses_async_sqlite_driver():
    assert settings.DATABASE_URL.startswith("sqlite+aiosqlite://")
