import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel


async def list_channels(db: AsyncSession, *, active_only: bool = False) -> list[Channel]:
    query = select(Channel).order_by(Channel.name)
    if active_only:
        query = query.where(Channel.is_active.is_(True))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_channel(db: AsyncSession, channel_id: uuid.UUID) -> Channel | None:
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    return result.scalar_one_or_none()


async def get_channel_by_name(db: AsyncSession, name: str) -> Channel | None:
    result = await db.execute(select(Channel).where(Channel.name == name))
    return result.scalar_one_or_none()


async def create_channel(db: AsyncSession, *, name: str) -> Channel:
    channel = Channel(id=uuid.uuid4(), name=name)
    db.add(channel)
    await db.flush()
    return channel
