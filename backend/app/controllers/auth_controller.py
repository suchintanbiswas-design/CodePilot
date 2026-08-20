"""Auth controller — thin orchestration layer between routes and services."""

from __future__ import annotations

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import ApiResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService


async def register(
    data: RegisterRequest,
    db: AsyncSession,
    redis: Redis,
) -> ApiResponse[UserResponse]:
    """Register a new user account."""
    service = AuthService(db, redis)
    user = await service.register(data)
    return ApiResponse(success=True, data=user, message="Registration successful")


async def login(
    data: LoginRequest,
    db: AsyncSession,
    redis: Redis,
) -> ApiResponse[TokenResponse]:
    """Authenticate user and return JWT tokens."""
    service = AuthService(db, redis)
    tokens = await service.login(data)
    return ApiResponse(success=True, data=tokens, message="Login successful")


async def refresh(
    data: RefreshRequest,
    db: AsyncSession,
    redis: Redis,
) -> ApiResponse[TokenResponse]:
    """Refresh an expired access token."""
    service = AuthService(db, redis)
    tokens = await service.refresh_token(data.refresh_token)
    return ApiResponse(success=True, data=tokens, message="Token refreshed")


async def logout(
    token: str,
    db: AsyncSession,
    redis: Redis,
) -> ApiResponse[None]:
    """Blacklist current token and logout."""
    service = AuthService(db, redis)
    await service.logout(token)
    return ApiResponse(success=True, message="Logout successful")


async def me(
    token: str,
    db: AsyncSession,
    redis: Redis,
) -> ApiResponse[UserResponse]:
    """Get the currently authenticated user."""
    service = AuthService(db, redis)
    user = await service.get_current_user(token)
    return ApiResponse(success=True, data=user)
