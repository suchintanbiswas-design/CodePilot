import logging
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import ForbiddenException, UnauthorizedException
from app.utils.security import decode_token

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_current_user_token), db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        repo = UserRepository(db)
        user = await repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")
        return user
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise UnauthorizedException("Could not validate credentials")


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise ForbiddenException("Requires admin privileges")
    return user
