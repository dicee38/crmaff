import base64
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.rbac import CAN_ASSIGN_MANAGER, CAN_EDIT_LEAD, CAN_VIEW_ALL_LEADS
from app.crud.lead import create_lead, get_lead, list_leads, update_lead
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.lead import LeadAssign, LeadCreate, LeadListResponse, LeadOut, LeadUpdate
from app.services.audit import write_audit_log

router = APIRouter(prefix="/leads", tags=["leads"])


def _encode_cursor(dt: datetime) -> str:
    return base64.urlsafe_b64encode(dt.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    try:
        return datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor") from exc


@router.get("", response_model=LeadListResponse)
async def list_leads_endpoint(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    geo: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadListResponse:
    decoded_cursor = _decode_cursor(cursor) if cursor else None

    # RBAC: sales_manager видит только своих лидов.
    manager_filter = None
    if current_user.role not in CAN_VIEW_ALL_LEADS:
        if current_user.role != UserRole.sales_manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        manager_filter = current_user.id

    leads = await list_leads(
        db,
        cursor=decoded_cursor,
        limit=limit + 1,
        manager_id=manager_filter,
        geo=geo,
        status=status_filter,
    )

    next_cursor = None
    if len(leads) > limit:
        leads = leads[:limit]
        next_cursor = _encode_cursor(leads[-1].created_at)

    return LeadListResponse(items=[LeadOut.model_validate(lead) for lead in leads], next_cursor=next_cursor)


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def create_lead_endpoint(
    payload: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_EDIT_LEAD)),
) -> LeadOut:
    lead = await create_lead(db, payload)
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="lead_created_manual",
        entity_type="lead",
        entity_id=str(lead.lead_id),
        meta=payload.model_dump(mode="json", exclude_unset=True),
    )
    await db.commit()
    return LeadOut.model_validate(lead)


async def _get_lead_or_404(db: AsyncSession, lead_id: uuid.UUID):
    lead = await get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


def _assert_can_view(current_user: User, lead) -> None:
    if current_user.role in CAN_VIEW_ALL_LEADS:
        return
    if current_user.role == UserRole.sales_manager and lead.assigned_manager_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def _assert_can_edit(current_user: User, lead) -> None:
    if current_user.role in (UserRole.admin, UserRole.affiliate_manager):
        return
    if current_user.role == UserRole.sales_manager and lead.assigned_manager_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead_endpoint(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadOut:
    lead = await _get_lead_or_404(db, lead_id)
    _assert_can_view(current_user, lead)
    return LeadOut.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead_endpoint(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadOut:
    lead = await _get_lead_or_404(db, lead_id)
    _assert_can_edit(current_user, lead)

    before = {"status": lead.status.value, "assigned_manager_id": str(lead.assigned_manager_id)}
    lead = await update_lead(db, lead, payload)

    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="lead_updated",
        entity_type="lead",
        entity_id=str(lead.lead_id),
        meta={"before": before, "changes": payload.model_dump(mode="json", exclude_unset=True)},
    )
    await db.commit()
    return LeadOut.model_validate(lead)


@router.post("/{lead_id}/assign", response_model=LeadOut)
async def assign_lead_endpoint(
    lead_id: uuid.UUID,
    payload: LeadAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_ASSIGN_MANAGER)),
) -> LeadOut:
    lead = await _get_lead_or_404(db, lead_id)
    previous_manager_id = lead.assigned_manager_id
    lead = await update_lead(db, lead, LeadUpdate(assigned_manager_id=payload.manager_id))

    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="manager_assigned",
        entity_type="lead",
        entity_id=str(lead.lead_id),
        meta={
            "previous_manager_id": str(previous_manager_id) if previous_manager_id else None,
            "new_manager_id": str(payload.manager_id),
        },
    )
    await db.commit()
    return LeadOut.model_validate(lead)
