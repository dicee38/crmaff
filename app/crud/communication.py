import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import Communication


async def list_communications_by_lead(
    db: AsyncSession, lead_id: uuid.UUID, *, limit: int = 50
) -> list[Communication]:
    result = await db.execute(
        select(Communication)
        .where(Communication.lead_id == lead_id)
        .order_by(Communication.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
