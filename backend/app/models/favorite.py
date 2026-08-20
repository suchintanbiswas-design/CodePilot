from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.favorite_collection import FavoriteCollection
    from app.models.review import Review
    from app.models.user import User


class Favorite(Base, UUIDMixin):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "review_id", name="uq_user_review_favorite"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    review_id: Mapped[UUID] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE")
    )
    collection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("favorite_collections.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="favorites")
    review: Mapped["Review"] = relationship(back_populates="favorites")
    collection: Mapped["FavoriteCollection"] = relationship(back_populates="favorites")
