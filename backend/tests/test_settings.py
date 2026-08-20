from unittest.mock import patch
import pytest
from httpx import AsyncClient
from app.main import app
from app.middleware.auth import get_current_user
from app.models.user import User
import uuid

@pytest.fixture
def auth_override():
    user = User(id=uuid.uuid4(), email="test@example.com")
    async def override():
        return user
    app.dependency_overrides[get_current_user] = override
    yield user
    # Don't clear all, just pop this one if needed, or rely on get_db to clear all

@pytest.mark.asyncio
async def test_update_preferences(client: AsyncClient, override_get_db, auth_override):
    with patch("app.services.user_service.UserService.update_preferences") as mock_update:
        mock_update.return_value = {"defaultLanguage": "Rust"}
        
        response = await client.put(
            "/api/v1/users/me/preferences",
            json={"defaultLanguage": "Rust"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, override_get_db, auth_override):
    with patch("app.services.user_service.UserService.change_password") as mock_change:
        mock_change.return_value = True
        
        response = await client.put(
            "/api/v1/users/me/password",
            json={"current_password": "oldpassword", "new_password": "newpassword"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_change_password_fail(client: AsyncClient, override_get_db, auth_override):
    with patch("app.services.user_service.UserService.change_password") as mock_change:
        mock_change.return_value = False
        
        response = await client.put(
            "/api/v1/users/me/password",
            json={"current_password": "oldpassword", "new_password": "newpassword"}
        )
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_soft_delete(client: AsyncClient, override_get_db, auth_override):
    with patch("app.services.user_service.UserService.delete_account") as mock_del:
        mock_del.return_value = True
        
        response = await client.delete("/api/v1/users/me")
        assert response.status_code == 200
