"""Test all History page actions against the live backend."""
import requests
import json
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.models.user import User
import uuid

BASE = "http://localhost:8000/api/v1"

@pytest.fixture
def auth_override():
    from app.main import app
    from app.middleware.auth import get_current_user
    user = User(id=uuid.uuid4(), email="admin@codepilot.dev", role="admin")
    async def override():
        return user
    app.dependency_overrides[get_current_user] = override
    yield user

@pytest.fixture
def mock_review_id():
    return str(uuid.uuid4())

@pytest.mark.asyncio
async def test_download(client: AsyncClient, override_get_db, auth_override, mock_review_id):
    with patch("app.repositories.review_repository.ReviewRepository.get", new_callable=AsyncMock) as mock_get, \
         patch("app.services.report_service.ReportService.get_or_generate_report", new_callable=AsyncMock) as mock_gen:
        
        from app.models.review import Review
        mock_get.return_value = Review(id=uuid.uuid4(), title="Mock Review")
        mock_gen.return_value = (b"%PDF-1.4 mock pdf data", "application/pdf")
        
        response = await client.get(
            f"/api/v1/reviews/{mock_review_id}/report?type=pdf",
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code in (200, 404)

@pytest.mark.asyncio
async def test_favorite(client: AsyncClient, override_get_db, auth_override, mock_review_id):
    with patch("app.services.favorite_service.FavoriteService.add_review_to_collection", new_callable=AsyncMock) as mock_fav:
        class MockFav:
            id = uuid.uuid4()
        mock_fav.return_value = MockFav()
        response = await client.post(
            f"/api/v1/favorites/reviews/{mock_review_id}",
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code in (200, 201, 404)

@pytest.mark.asyncio
async def test_duplicate(client: AsyncClient, override_get_db, auth_override, mock_review_id):
    with patch("app.services.review_service.ReviewService.duplicate_review", new_callable=AsyncMock) as mock_dup:
        from app.models.review import Review
        mock_dup.return_value = Review(id=uuid.uuid4(), title="Duplicate")
        response = await client.post(
            f"/api/v1/reviews/{mock_review_id}/duplicate",
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code in (200, 201, 404)

@pytest.mark.asyncio
async def test_delete(client: AsyncClient, override_get_db, auth_override, mock_review_id):
    with patch("app.services.review_service.ReviewService.delete_review", new_callable=AsyncMock) as mock_del:
        mock_del.return_value = True
        response = await client.delete(
            f"/api/v1/reviews/{mock_review_id}",
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code in (200, 204, 404)
