from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent


class AuditService:
    async def write(
        self,
        db: AsyncSession,
        *,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event = AuditEvent(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        db.add(event)
