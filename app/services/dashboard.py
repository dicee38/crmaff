"""Воронка click -> lead -> manager -> registration -> ftd -> commission
(см. CLAUDE.md, "Сквозная цепочка") и базовые KPI.

Стадии registered/ftd/commission считаются по реально полученным
affiliate_events (postback ИЛИ manual), а не по текущему lead.status -
статус лида может уйти дальше (напр. active), но факт регистрации/FTD
остаётся зафиксированным событием и не должен теряться из воронки.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate_event import AffiliateEvent
from app.models.enums import AffiliateEventType, TrackingEventType
from app.models.lead import Lead
from app.models.tracking_event import TrackingEvent


def _apply_common_filters(query, column, *, date_from: datetime | None, date_to: datetime | None):
    if date_from is not None:
        query = query.where(column >= date_from)
    if date_to is not None:
        query = query.where(column <= date_to)
    return query


async def compute_funnel(
    db: AsyncSession,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    geo: str | None = None,
) -> dict:
    click_query = select(func.count()).select_from(TrackingEvent).where(
        TrackingEvent.event_type == TrackingEventType.click
    )
    click_query = _apply_common_filters(click_query, TrackingEvent.event_timestamp, date_from=date_from, date_to=date_to)
    if geo is not None:
        click_query = click_query.join(Lead, Lead.lead_id == TrackingEvent.lead_id).where(Lead.geo == geo)
    clicks = (await db.execute(click_query)).scalar_one()

    lead_query = select(func.count()).select_from(Lead)
    lead_query = _apply_common_filters(lead_query, Lead.created_at, date_from=date_from, date_to=date_to)
    if geo is not None:
        lead_query = lead_query.where(Lead.geo == geo)
    leads_created = (await db.execute(lead_query)).scalar_one()

    manager_query = lead_query.where(Lead.assigned_manager_id.isnot(None))
    manager_assigned = (await db.execute(manager_query)).scalar_one()

    async def _distinct_lead_count(event_type: AffiliateEventType) -> int:
        query = select(func.count(func.distinct(AffiliateEvent.lead_id))).where(
            AffiliateEvent.event_type == event_type, AffiliateEvent.lead_id.isnot(None)
        )
        query = _apply_common_filters(query, AffiliateEvent.received_at, date_from=date_from, date_to=date_to)
        if geo is not None:
            query = query.join(Lead, Lead.lead_id == AffiliateEvent.lead_id).where(Lead.geo == geo)
        return (await db.execute(query)).scalar_one()

    registered = await _distinct_lead_count(AffiliateEventType.registration)
    ftd = await _distinct_lead_count(AffiliateEventType.ftd)

    commission_query = select(func.coalesce(func.sum(AffiliateEvent.amount), 0)).where(
        AffiliateEvent.event_type.in_(
            [AffiliateEventType.ftd.value, AffiliateEventType.deposit.value, AffiliateEventType.commission.value]
        )
    )
    commission_query = _apply_common_filters(
        commission_query, AffiliateEvent.received_at, date_from=date_from, date_to=date_to
    )
    if geo is not None:
        commission_query = commission_query.join(Lead, Lead.lead_id == AffiliateEvent.lead_id).where(Lead.geo == geo)
    commission_total = (await db.execute(commission_query)).scalar_one()

    return {
        "clicks": clicks,
        "leads_created": leads_created,
        "manager_assigned": manager_assigned,
        "registered": registered,
        "ftd": ftd,
        "commission_total": Decimal(commission_total),
    }


def _pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


async def compute_kpi(
    db: AsyncSession,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    geo: str | None = None,
) -> dict:
    funnel = await compute_funnel(db, date_from=date_from, date_to=date_to, geo=geo)

    return {
        "total_leads": funnel["leads_created"],
        "total_registered": funnel["registered"],
        "total_ftd": funnel["ftd"],
        "total_revenue": funnel["commission_total"],
        "lead2reg_pct": _pct(funnel["registered"], funnel["leads_created"]),
        "reg2fd_pct": _pct(funnel["ftd"], funnel["registered"]),
    }
