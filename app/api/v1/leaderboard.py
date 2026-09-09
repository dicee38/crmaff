from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.leaderboard import LeaderboardResponse
from app.services.leaderboard import METRICS, compute_leaderboard

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard_endpoint(
    metric: str = Query(default="cashflow", pattern="^(cashflow|fd_revenue_per_lead|lead_to_fd|fd_to_rd)$"),
    period: str = Query(default="week", pattern="^(week|month)$"),
    channel_group: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaderboardResponse:
    # Открыт всем ролям (мотивационный инструмент) - см. RBAC-матрицу CLAUDE.md,
    # строка "Лидерборд" отмечена ✓ для всех ролей без исключения.
    assert metric in METRICS  # защита от рассинхрона pattern <-> METRICS

    data = await compute_leaderboard(
        db,
        metric=metric,
        period=period,
        channel_group=channel_group,
        current_user_id=current_user.id,
    )
    return LeaderboardResponse(**data)
