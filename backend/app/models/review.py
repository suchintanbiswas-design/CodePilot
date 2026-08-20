from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

if TYPE_CHECKING:
    from app.models.favorite import Favorite
    from app.models.language import Language
    from app.models.report import Report
    from app.models.user import User


class Review(Base, BaseMixin):
    __tablename__ = "reviews"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    language_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("languages.id"))
    title: Mapped[str] = mapped_column(String(255), index=True)
    source_code: Mapped[str] = mapped_column(Text)
    improved_code: Mapped[Optional[str]] = mapped_column(Text)
    issues: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, server_default="[]")
    quality_score: Mapped[Optional[int]] = mapped_column()
    review_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSONB, server_default="{}"
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    file_size: Mapped[Optional[int]] = mapped_column()
    repo_url: Mapped[Optional[str]] = mapped_column(String(1024), index=True)

    user: Mapped["User"] = relationship(back_populates="reviews")
    language: Mapped["Language"] = relationship(back_populates="reviews")
    reports: Mapped[List["Report"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )
    favorites: Mapped[List["Favorite"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )
