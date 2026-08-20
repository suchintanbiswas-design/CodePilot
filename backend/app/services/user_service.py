import json
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserService:
    def __init__(self):
        pass

    async def get_profile(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def update_profile(
        self, db: AsyncSession, user_id: UUID, update_data: dict
    ) -> Optional[User]:
        user = await self.get_profile(db, user_id)
        if not user:
            return None

        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await db.commit()
        await db.refresh(user)
        return user

    async def update_preferences(
        self, db: AsyncSession, user_id: UUID, preferences: dict
    ) -> dict:
        from app.models.settings import UserSettings
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await db.execute(stmt)
        settings = result.scalars().first()
        
        if not settings:
            settings = UserSettings(user_id=user_id, preferences={})
            db.add(settings)
            
        settings.preferences = preferences
        await db.commit()
        return settings.preferences

    async def change_password(
        self, db: AsyncSession, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        from app.utils.security import verify_password, hash_password
        user = await self.get_profile(db, user_id)
        if not user:
            return False
            
        if not verify_password(current_password, user.password_hash):
            return False
            
        user.password_hash = hash_password(new_password)
        
        # Create security notification
        from app.models.notification import Notification
        import uuid
        
        notif = Notification(
            user_id=user_id,
            title="Security Alert",
            message="Your password was successfully changed.",
            type="security",
            reference_id=f"pwd_{uuid.uuid4()}"
        )
        db.add(notif)
        
        await db.commit()
        return True

    def export_user_data(self, user: User) -> str:
        # Synchronous JSON export (explicitly excluding password_hash, tokens, secrets)
        data = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "bio": user.bio,
            "github_profile": user.github_profile,
            "linkedin_profile": user.linkedin_profile,
            "preferred_languages": user.preferred_languages,
            "role": user.role,
            "is_active": user.is_active,
        }
        return json.dumps(data)

    async def delete_account(self, db: AsyncSession, user_id: UUID) -> bool:
        # SOFT DELETE
        user = await self.get_profile(db, user_id)
        if not user:
            return False
        user.is_active = False
        await db.commit()
        return True
