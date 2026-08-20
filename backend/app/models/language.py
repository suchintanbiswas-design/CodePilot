from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.review import Review


class Language(Base, UUIDMixin):
    __tablename__ = "languages"

    name: Mapped[str] = mapped_column(String(50), unique=True)
    extension: Mapped[str] = mapped_column(String(20))
    icon: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    reviews: Mapped[List["Review"]] = relationship(back_populates="language")
