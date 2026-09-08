import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate_event import AffiliateEvent


async def list_affiliate_events_by_lead(
    db: AsyncSession, lead_id: uuid.UUID, *, limit: int = 50
) -> list[AffiliateEvent]:
    result = await db.execute(
        select(AffiliateEvent)
        .where(AffiliateEvent.lead_id == lead_id)
        .order_by(AffiliateEvent.received_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
