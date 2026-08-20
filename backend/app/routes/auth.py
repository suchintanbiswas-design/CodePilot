"""Authentication routes — register, login, refresh, logout, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.redis import get_redis
from app.controllers import auth_controller
from app.middleware.auth import get_current_user_token
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import ApiResponse
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=201)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Register a new user account."""
    return await auth_controller.register(data, db, redis)


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Authenticate user and return JWT tokens."""
    return await auth_controller.login(data, db, redis)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Refresh an expired access token."""
    return await auth_controller.refresh(data, db, redis)


@router.post("/logout", response_model=ApiResponse[None])
async def logout(
    token: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Blacklist current token and log out."""
    return await auth_controller.logout(token, db, redis)


@router.get("/me", response_model=ApiResponse[UserResponse])
async def me(
    token: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Get the currently authenticated user."""
    return await auth_controller.me(token, db, redis)
