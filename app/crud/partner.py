import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partner import Partner


async def list_partners(db: AsyncSession, *, active_only: bool = False) -> list[Partner]:
    query = select(Partner).order_by(Partner.name)
    if active_only:
        query = query.where(Partner.is_active.is_(True))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_partner(db: AsyncSession, partner_id: uuid.UUID) -> Partner | None:
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    return result.scalar_one_or_none()


async def get_partner_by_name(db: AsyncSession, name: str) -> Partner | None:
    result = await db.execute(select(Partner).where(Partner.name == name))
    return result.scalar_one_or_none()


async def create_partner(db: AsyncSession, *, name: str) -> Partner:
    partner = Partner(id=uuid.uuid4(), name=name)
    db.add(partner)
    await db.flush()
    return partner
