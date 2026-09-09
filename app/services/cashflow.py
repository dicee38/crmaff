"""Cashflow-отчётность по МОП (см. CLAUDE.md, раздел "Cashflow-отчётность
по МОП").

Упрощение по группировке: полноценная многоуровневая группировка (МОП x
период x канал одновременно) не реализована - group_by принимает одно
измерение ("manager" или "channel"), а период задаётся фильтром
date_from/date_to (прогнать отчёт за нужную неделю/месяц). Дерево
"общий итог сверху + разбивка ниже" - ровно два уровня, как описано в
спеке ("общий итог сверху, разбивка по МОП ниже").
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate_event import AffiliateEvent
from app.models.enums import AffiliateEventType
from app.models.lead import Lead
from app.models.user import User


def _pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


async def _reg_fd_rd_counts(
    db: AsyncSession,
    *,
    manager_id: uuid.UUID | None,
    channel: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> dict:
    def _scoped(query):
        if manager_id is not None or channel is not None:
            query = query.join(Lead, Lead.lead_id == AffiliateEvent.lead_id)
            if manager_id is not None:
                query = query.where(Lead.assigned_manager_id == manager_id)
        if channel is not None:
            query = query.where(AffiliateEvent.channel == channel)
        if date_from is not None:
            query = query.where(AffiliateEvent.received_at >= date_from)
        if date_to is not None:
            query = query.where(AffiliateEvent.received_at <= date_to)
        return query

    reg_query = _scoped(
        select(func.count(func.distinct(AffiliateEvent.lead_id))).where(
            AffiliateEvent.event_type == AffiliateEventType.registration
        )
    )
    reg = (await db.execute(reg_query)).scalar_one()

    fd_query = _scoped(
        select(func.count(), func.coalesce(func.sum(AffiliateEvent.amount), 0)).where(
            AffiliateEvent.event_type == AffiliateEventType.ftd
        )
    )
    fd_count, fd_sum = (await db.execute(fd_query)).one()

    rd_query = _scoped(
        select(func.count(), func.coalesce(func.sum(AffiliateEvent.amount), 0)).where(
            AffiliateEvent.event_type == AffiliateEventType.deposit
        )
    )
    rd_count, rd_sum = (await db.execute(rd_query)).one()

    return {
        "reg": reg,
        "fd_count": fd_count,
        "fd_sum": Decimal(fd_sum),
        "rd_count": rd_count,
        "rd_sum": Decimal(rd_sum),
    }


async def _total_leads_for_manager(
    db: AsyncSession, manager_id: uuid.UUID, *, date_from: datetime | None, date_to: datetime | None
) -> int:
    query = select(func.count()).select_from(Lead).where(Lead.assigned_manager_id == manager_id)
    if date_from is not None:
        query = query.where(Lead.created_at >= date_from)
    if date_to is not None:
        query = query.where(Lead.created_at <= date_to)
    return (await db.execute(query)).scalar_one()


def _row(counts: dict, *, total_leads: int | None) -> dict:
    row = {
        "reg": counts["reg"],
        "fd_count": counts["fd_count"],
        "fd_sum": counts["fd_sum"],
        "rd_count": counts["rd_count"],
        "rd_sum": counts["rd_sum"],
        "cashflow": counts["fd_sum"] + counts["rd_sum"],
        "reg2fd_pct": _pct(counts["fd_count"], counts["reg"]),
    }
    row["lead2reg_pct"] = _pct(counts["reg"], total_leads) if total_leads is not None else None
    return row


async def compute_mop_cashflow(
    db: AsyncSession,
    *,
    group_by: str = "manager",
    manager_id: uuid.UUID | None = None,
    channel: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    scope_manager_id: uuid.UUID | None = None,
) -> dict:
    """scope_manager_id - принудительный фильтр (для sales_manager: только
    свои данные, независимо от переданных group_by/manager_id)."""
    effective_manager_filter = scope_manager_id if scope_manager_id is not None else manager_id

    total_counts = await _reg_fd_rd_counts(
        db, manager_id=effective_manager_filter, channel=channel, date_from=date_from, date_to=date_to
    )
    total_leads = None
    if effective_manager_filter is not None:
        total_leads = await _total_leads_for_manager(
            db, effective_manager_filter, date_from=date_from, date_to=date_to
        )
    total_row = _row(total_counts, total_leads=total_leads)

    groups: list[dict] = []

    if scope_manager_id is not None:
        # sales_manager видит только свои данные - без разбивки по группам.
        return {"total": total_row, "groups": []}

    if group_by == "manager":
        managers_result = await db.execute(
            select(Lead.assigned_manager_id).where(Lead.assigned_manager_id.isnot(None)).distinct()
        )
        manager_ids = [m for m in managers_result.scalars().all() if manager_id is None or m == manager_id]

        for m_id in manager_ids:
            counts = await _reg_fd_rd_counts(
                db, manager_id=m_id, channel=channel, date_from=date_from, date_to=date_to
            )
            m_total_leads = await _total_leads_for_manager(db, m_id, date_from=date_from, date_to=date_to)
            user_result = await db.execute(select(User).where(User.id == m_id))
            user = user_result.scalar_one_or_none()
            label = user.full_name if user else str(m_id)
            groups.append({"key": str(m_id), "label": label, **_row(counts, total_leads=m_total_leads)})

    elif group_by == "channel":
        channels_result = await db.execute(
            select(AffiliateEvent.channel).where(AffiliateEvent.channel.isnot(None)).distinct()
        )
        channels = [c for c in channels_result.scalars().all() if channel is None or c == channel]

        for ch in channels:
            counts = await _reg_fd_rd_counts(
                db, manager_id=manager_id, channel=ch, date_from=date_from, date_to=date_to
            )
            # lead2reg_pct не считается для группировки по каналу - у лида
            # нет собственного поля "канал" (оно есть только на событиях).
            groups.append({"key": ch, "label": ch, **_row(counts, total_leads=None)})

    return {"total": total_row, "groups": groups}
