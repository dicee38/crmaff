from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.rbac import CAN_VIEW_REVENUE
from app.database import get_db
from app.schemas.dashboard import FunnelResponse, KpiResponse
from app.services.dashboard import compute_funnel, compute_kpi

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/funnel", response_model=FunnelResponse)
async def get_funnel_endpoint(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    geo: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_roles(*CAN_VIEW_REVENUE)),
) -> FunnelResponse:
    data = await compute_funnel(db, date_from=date_from, date_to=date_to, geo=geo)
    return FunnelResponse(**data)


@router.get("/kpi", response_model=KpiResponse)
async def get_kpi_endpoint(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    geo: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_roles(*CAN_VIEW_REVENUE)),
) -> KpiResponse:
    data = await compute_kpi(db, date_from=date_from, date_to=date_to, geo=geo)
    return KpiResponse(**data)
