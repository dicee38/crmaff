import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.cashflow import CashflowReportResponse
from app.services.cashflow import compute_mop_cashflow

router = APIRouter(prefix="/reports", tags=["reports"])

# Cashflow-отчёт по команде: admin/affiliate_manager/mop_lead/analyst видят всю
# команду; sales_manager - только свои данные (без разбивки по группам);
# compliance и остальные роли доступа не имеют (см. RBAC-матрицу CLAUDE.md).
_FULL_VISIBILITY_ROLES = {UserRole.admin, UserRole.affiliate_manager, UserRole.mop_lead, UserRole.analyst}


@router.get("/mop-cashflow", response_model=CashflowReportResponse)
async def mop_cashflow_report_endpoint(
    group_by: str = Query(default="manager", pattern="^(manager|channel)$"),
    manager_id: uuid.UUID | None = Query(default=None),
    channel: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CashflowReportResponse:
    scope_manager_id = None
    if current_user.role not in _FULL_VISIBILITY_ROLES:
        if current_user.role != UserRole.sales_manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        scope_manager_id = current_user.id

    data = await compute_mop_cashflow(
        db,
        group_by=group_by,
        manager_id=manager_id,
        channel=channel,
        date_from=date_from,
        date_to=date_to,
        scope_manager_id=scope_manager_id,
    )
    return CashflowReportResponse(**data)
