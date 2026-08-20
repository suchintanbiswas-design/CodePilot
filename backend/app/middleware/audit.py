import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_audit(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    metadata_: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_=metadata_ or {},
        ip_address=ip_address,
    )
    db.add(log_entry)
    await db.commit()
