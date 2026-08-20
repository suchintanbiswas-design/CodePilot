from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import GenericRepository


class UserRepository(GenericRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_users(
        self, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[User]:
        stmt = select(User)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_term),
                    User.username.ilike(search_term),
                    User.full_name.ilike(search_term),
                )
            )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_last_login(self, user_id: UUID) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = func.now()
            await self.session.flush()
