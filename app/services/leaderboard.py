"""Лидерборд МОП (см. CLAUDE.md, раздел "Лидерборд").

Метрики считаются переиспользованием того же агрегата, что и в
cashflow-отчёте (REG/FD/RD по менеджеру), чтобы не дублировать логику
подсчёта и не разъезжаться в семантике между отчётом и лидербордом.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.user import User
from app.services.cashflow import reg_fd_rd_counts, total_leads_for_manager

METRICS = {"cashflow", "fd_revenue_per_lead", "lead_to_fd", "fd_to_rd"}


def period_to_date_range(period: str) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if period == "month":
        date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # "week" - по умолчанию
        date_from = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return date_from, now


def _metric_value(metric: str, counts: dict, total_leads: int) -> Decimal:
    if metric == "cashflow":
        return counts["fd_sum"] + counts["rd_sum"]
    if metric == "fd_revenue_per_lead":
        if total_leads == 0:
            return Decimal(0)
        return (counts["fd_sum"] / total_leads).quantize(Decimal("0.01"))
    if metric == "lead_to_fd":
        if total_leads == 0:
            return Decimal(0)
        return Decimal(round(counts["fd_count"] / total_leads * 100, 2))
    if metric == "fd_to_rd":
        if counts["fd_count"] == 0:
            return Decimal(0)
        return Decimal(round(counts["rd_count"] / counts["fd_count"] * 100, 2))
    raise ValueError(f"Unknown metric: {metric}")


async def compute_leaderboard(
    db: AsyncSession,
    *,
    metric: str,
    period: str,
    channel_group: str | None,
    current_user_id: uuid.UUID | None,
) -> dict:
    date_from, date_to = period_to_date_range(period)

    managers_result = await db.execute(
        select(Lead.assigned_manager_id).where(Lead.assigned_manager_id.isnot(None)).distinct()
    )
    manager_ids = list(managers_result.scalars().all())

    entries = []
    for manager_id in manager_ids:
        counts = await reg_fd_rd_counts(
            db, manager_id=manager_id, channel=channel_group, date_from=date_from, date_to=date_to
        )
        total_leads = await total_leads_for_manager(db, manager_id, date_from=date_from, date_to=date_to)
        value = _metric_value(metric, counts, total_leads)

        user_result = await db.execute(select(User).where(User.id == manager_id))
        user = user_result.scalar_one_or_none()
        label = user.full_name if user else str(manager_id)

        entries.append({"manager_id": manager_id, "label": label, "value": value})

    entries.sort(key=lambda e: e["value"], reverse=True)
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    current_user_rank = None
    for entry in entries:
        if entry["manager_id"] == current_user_id:
            current_user_rank = entry["rank"]
            break

    visible_ranks: set[int] = {1, 2, 3}
    if current_user_rank is not None:
        visible_ranks |= {current_user_rank - 1, current_user_rank, current_user_rank + 1}
    visible_ranks = {r for r in visible_ranks if 1 <= r <= len(entries)}

    rows = [
        {**entry, "is_current_user": entry["manager_id"] == current_user_id}
        for entry in entries
        if entry["rank"] in visible_ranks
    ]

    delta_to_rank_above = None
    delta_over_rank_below = None
    if current_user_rank is not None:
        current_value = entries[current_user_rank - 1]["value"]
        if current_user_rank > 1:
            delta_to_rank_above = entries[current_user_rank - 2]["value"] - current_value
        if current_user_rank < len(entries):
            delta_over_rank_below = current_value - entries[current_user_rank]["value"]

    return {
        "metric": metric,
        "period": period,
        "total_participants": len(entries),
        "rows": rows,
        "current_user_rank": current_user_rank,
        "delta_to_rank_above": delta_to_rank_above,
        "delta_over_rank_below": delta_over_rank_below,
    }
