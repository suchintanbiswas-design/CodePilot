from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.schemas.auth import TokenResponse


@pytest.mark.asyncio
async def test_register_valid(client: AsyncClient, override_get_db):
    with patch("app.services.auth_service.AuthService.register") as mock_register:
        from datetime import datetime
        import uuid
        mock_register.return_value = {
            "id": uuid.uuid4(), 
            "email": "test@example.com", 
            "username": "testuser",
            "role": "user",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "username": "testuser", "password": "password123"}
        )
        assert response.status_code == 201

@pytest.mark.asyncio
async def test_login_valid(client: AsyncClient, override_get_db):
    with patch("app.services.auth_service.AuthService.login") as mock_login:
        mock_login.return_value = TokenResponse(access_token="access", refresh_token="refresh")
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json().get("data", {})

@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient, override_get_db):
    from app.utils.exceptions import UnauthorizedException
    with patch("app.services.auth_service.AuthService.login", side_effect=UnauthorizedException("Invalid credentials")):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
