from datetime import datetime
import uuid
from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseMixin, Base


class Notification(Base, BaseMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50))  # 'review_completed', 'review_failed', 'security'
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Using specific constraints or metadata for deduplication if needed
    reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    user = relationship("User")
