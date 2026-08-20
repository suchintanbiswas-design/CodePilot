import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.settings import UserSettings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.utils.exceptions import ConflictException, UnauthorizedException
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.user_repo = UserRepository(db)

    async def register(self, data: RegisterRequest) -> UserResponse:
        existing_email = await self.user_repo.get_by_email(data.email)
        if existing_email:
            raise ConflictException("Email already registered")

        existing_username = await self.user_repo.get_by_username(data.username)
        if existing_username:
            raise ConflictException("Username already taken")

        user = User(
            email=data.email,
            username=data.username,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
        )
        await self.user_repo.create(user)

        user_settings = UserSettings(user_id=user.id)
        self.db.add(user_settings)
        await self.db.commit()
        await self.db.refresh(user)

        return UserResponse.model_validate(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException("Invalid credentials")

        if not user.is_active:
            raise UnauthorizedException("Account is disabled")

        await self.user_repo.update_last_login(user.id)
        await self.db.commit()

        token_data = {"sub": str(user.id)}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        is_blacklisted = await self.redis.get(f"bl:{refresh_token}")
        if is_blacklisted:
            raise UnauthorizedException("Token revoked")

        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        user = await self.user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        # Optionally blacklist old refresh token here
        await self.redis.setex(
            f"bl:{refresh_token}", settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400, "1"
        )

        token_data = {"sub": str(user.id)}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def get_current_user(self, token: str) -> UserResponse:
        is_blacklisted = await self.redis.get(f"bl:{token}")
        if is_blacklisted:
            raise UnauthorizedException("Token revoked")

        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        user = await self.user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        return UserResponse.model_validate(user)

    async def logout(self, token: str) -> None:
        payload = decode_token(token)
        exp = payload.get("exp", 0)
        import time

        ttl = max(1, int(exp - time.time()))
        await self.redis.setex(f"bl:{token}", ttl, "1")
