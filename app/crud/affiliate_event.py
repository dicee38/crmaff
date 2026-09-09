import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate_event import AffiliateEvent
from app.models.enums import AffiliateEventSource, AffiliateEventType


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


async def get_affiliate_event_by_external_id(db: AsyncSession, external_event_id: str) -> AffiliateEvent | None:
    result = await db.execute(
        select(AffiliateEvent).where(AffiliateEvent.external_event_id == external_event_id)
    )
    return result.scalar_one_or_none()


async def create_affiliate_event(
    db: AsyncSession,
    *,
    lead_id: uuid.UUID | None,
    partner: str,
    external_event_id: str,
    event_type: AffiliateEventType,
    source: AffiliateEventSource = AffiliateEventSource.postback,
    entered_by: uuid.UUID | None = None,
    channel: str | None = None,
    amount: Decimal | None = None,
    currency: str | None = None,
    raw_payload: dict,
    normalized_payload: dict | None = None,
    validation_flags: dict | None = None,
) -> AffiliateEvent:
    event = AffiliateEvent(
        id=uuid.uuid4(),
        lead_id=lead_id,
        partner=partner,
        external_event_id=external_event_id,
        event_type=event_type,
        source=source,
        entered_by=entered_by,
        channel=channel,
        amount=amount,
        currency=currency,
        raw_payload=raw_payload,
        normalized_payload=normalized_payload,
        validation_flags=validation_flags,
        processed_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.flush()
    return event
