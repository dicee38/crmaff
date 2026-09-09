import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
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
    received_at: datetime | None = None,
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
    if received_at is not None:
        event.received_at = received_at
    db.add(event)
    await db.flush()
    return event


async def find_possible_duplicate(
    db: AsyncSession,
    *,
    lead_id: uuid.UUID,
    event_type: AffiliateEventType,
    amount: Decimal | None,
    occurred_on: date,
) -> AffiliateEvent | None:
    """Тот же лид + тип действия + сумма + дата (без учёта времени) - см.
    правило possible_duplicate в CLAUDE.md (не блокирует сохранение)."""
    result = await db.execute(
        select(AffiliateEvent).where(
            AffiliateEvent.lead_id == lead_id,
            AffiliateEvent.event_type == event_type,
            AffiliateEvent.amount == amount,
            func.date(AffiliateEvent.received_at) == occurred_on,
        )
    )
    return result.scalars().first()


async def list_affiliate_events(
    db: AsyncSession,
    *,
    cursor: datetime | None = None,
    limit: int = 50,
    manager_lead_ids: list[uuid.UUID] | None = None,
    event_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    event_type: str | None = None,
    source: AffiliateEventSource | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
) -> list[AffiliateEvent]:
    query = select(AffiliateEvent).order_by(AffiliateEvent.received_at.desc(), AffiliateEvent.id.desc())
    query = _apply_action_filters(
        query,
        manager_lead_ids=manager_lead_ids,
        event_id=event_id,
        lead_id=lead_id,
        event_type=event_type,
        source=source,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
    )
    if cursor is not None:
        query = query.where(AffiliateEvent.received_at < cursor)

    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def aggregate_affiliate_events(
    db: AsyncSession,
    *,
    manager_lead_ids: list[uuid.UUID] | None = None,
    event_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    event_type: str | None = None,
    source: AffiliateEventSource | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
) -> dict:
    deposit_types = (AffiliateEventType.ftd.value, AffiliateEventType.deposit.value)

    base_query = select(AffiliateEvent)
    base_query = _apply_action_filters(
        base_query,
        manager_lead_ids=manager_lead_ids,
        event_id=event_id,
        lead_id=lead_id,
        event_type=event_type,
        source=source,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
    )

    total_query = select(func.count()).select_from(base_query.subquery())
    total_actions = (await db.execute(total_query)).scalar_one()

    lead_count_query = select(func.count(func.distinct(base_query.subquery().c.lead_id)))
    lead_count = (await db.execute(lead_count_query)).scalar_one()

    deposits_query = base_query.where(AffiliateEvent.event_type.in_(deposit_types))
    deposit_count_query = select(func.count()).select_from(deposits_query.subquery())
    deposit_count = (await db.execute(deposit_count_query)).scalar_one()

    deposit_sum_query = select(func.coalesce(func.sum(deposits_query.subquery().c.amount), 0))
    deposit_sum = (await db.execute(deposit_sum_query)).scalar_one()

    return {
        "total_actions": total_actions,
        "lead_count": lead_count,
        "deposit_count": deposit_count,
        "deposit_sum": deposit_sum,
    }


def _apply_action_filters(
    query,
    *,
    manager_lead_ids: list[uuid.UUID] | None,
    event_id: uuid.UUID | None,
    lead_id: uuid.UUID | None,
    event_type: str | None,
    source: AffiliateEventSource | None,
    date_from: datetime | None,
    date_to: datetime | None,
    amount_min: Decimal | None,
    amount_max: Decimal | None,
):
    if manager_lead_ids is not None:
        query = query.where(AffiliateEvent.lead_id.in_(manager_lead_ids))
    if event_id is not None:
        query = query.where(AffiliateEvent.id == event_id)
    if lead_id is not None:
        query = query.where(AffiliateEvent.lead_id == lead_id)
    if event_type is not None:
        query = query.where(AffiliateEvent.event_type == event_type)
    if source is not None:
        query = query.where(AffiliateEvent.source == source)
    if date_from is not None:
        query = query.where(AffiliateEvent.received_at >= date_from)
    if date_to is not None:
        query = query.where(AffiliateEvent.received_at <= date_to)
    if amount_min is not None:
        query = query.where(AffiliateEvent.amount >= amount_min)
    if amount_max is not None:
        query = query.where(AffiliateEvent.amount <= amount_max)
    return query
