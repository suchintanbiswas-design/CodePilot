from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserSettings(Base, UUIDMixin):
    __tablename__ = "settings"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    theme: Mapped[str] = mapped_column(String(20), default="system")
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    default_language: Mapped[Optional[str]] = mapped_column(String(50))
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="settings")
