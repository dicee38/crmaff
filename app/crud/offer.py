import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.offer import Offer


async def get_offer(db: AsyncSession, offer_id: uuid.UUID) -> Offer | None:
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    return result.scalar_one_or_none()
