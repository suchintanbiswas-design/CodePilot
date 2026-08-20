from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.favorite import Favorite
    from app.models.favorite_collection import FavoriteCollection
    from app.models.report import Report
    from app.models.review import Review
    from app.models.settings import UserSettings


class User(Base, BaseMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column()
    bio: Mapped[Optional[str]] = mapped_column(String(500))
    github_profile: Mapped[Optional[str]] = mapped_column(String(255))
    linkedin_profile: Mapped[Optional[str]] = mapped_column(String(255))
    preferred_languages: Mapped[Optional[list]] = mapped_column(
        JSONB, server_default="[]"
    )

    reviews: Mapped[List["Review"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorites: Mapped[List["Favorite"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorite_collections: Mapped[List["FavoriteCollection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    settings: Mapped[Optional["UserSettings"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
