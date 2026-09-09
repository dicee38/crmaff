import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import Communication
from app.models.enums import CommunicationChannel, CommunicationDirection


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


async def get_communication_by_external_message_id(
    db: AsyncSession, external_message_id: str
) -> Communication | None:
    result = await db.execute(
        select(Communication).where(Communication.external_message_id == external_message_id)
    )
    return result.scalar_one_or_none()


async def create_communication(
    db: AsyncSession,
    *,
    lead_id: uuid.UUID,
    manager_id: uuid.UUID | None,
    channel: CommunicationChannel,
    direction: CommunicationDirection,
    message_text: str | None,
    external_message_id: str | None = None,
    is_ai_suggested: bool = False,
) -> Communication:
    communication = Communication(
        id=uuid.uuid4(),
        lead_id=lead_id,
        manager_id=manager_id,
        channel=channel,
        direction=direction,
        message_text=message_text,
        external_message_id=external_message_id,
        is_ai_suggested=is_ai_suggested,
    )
    db.add(communication)
    await db.flush()
    return communication
