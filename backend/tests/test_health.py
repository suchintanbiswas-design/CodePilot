import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient, override_get_db):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]

@pytest.mark.asyncio
async def test_ready_check(client: AsyncClient, override_get_db):
    response = await client.get("/ready")
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "healthy"
    else:
        assert response.status_code == 503
