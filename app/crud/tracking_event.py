import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TrackingEventType
from app.models.tracking_event import TrackingEvent


async def create_tracking_event(
    db: AsyncSession,
    *,
    lead_id: uuid.UUID | None,
    event_type: TrackingEventType,
    click_id: str | None = None,
    session_id: str | None = None,
    campaign_id: str | None = None,
    adset_id: str | None = None,
    creative_id: str | None = None,
    landing_id: str | None = None,
    raw_payload: dict,
) -> TrackingEvent:
    event = TrackingEvent(
        id=uuid.uuid4(),
        lead_id=lead_id,
        event_type=event_type,
        click_id=click_id,
        session_id=session_id,
        campaign_id=campaign_id,
        adset_id=adset_id,
        creative_id=creative_id,
        landing_id=landing_id,
        raw_payload=raw_payload,
    )
    db.add(event)
    await db.flush()
    return event


async def get_first_click_event(db: AsyncSession, lead_id: uuid.UUID) -> TrackingEvent | None:
    result = await db.execute(
        select(TrackingEvent)
        .where(TrackingEvent.lead_id == lead_id, TrackingEvent.event_type == TrackingEventType.click)
        .order_by(TrackingEvent.event_timestamp.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()
