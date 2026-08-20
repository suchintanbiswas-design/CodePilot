from unittest.mock import AsyncMock, patch

import pytest

try:
    import pytest_asyncio
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.config.database import get_db
    from app.main import app

    _HAS_INTEGRATION_DEPS = True
except ImportError:
    _HAS_INTEGRATION_DEPS = False


if _HAS_INTEGRATION_DEPS:

    @pytest_asyncio.fixture
    async def client():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_db_session():
        mock_session = AsyncMock(spec=AsyncSession)
        return mock_session

    @pytest_asyncio.fixture
    async def override_get_db(mock_db_session):
        async def _get_db():
            yield mock_db_session
        app.dependency_overrides[get_db] = _get_db
        yield
        app.dependency_overrides.clear()

    @pytest.fixture
    def mock_redis():
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        return mock_client

    @pytest.fixture(autouse=True)
    def override_get_redis(mock_redis):
        with patch("app.main.get_redis", return_value=mock_redis):
            yield mock_redis

