import base64
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.rbac import CAN_ASSIGN_MANAGER, CAN_DELETE_RECORDS, CAN_EDIT_LEAD, CAN_VIEW_ALL_LEADS
from app.crud.affiliate_event import list_affiliate_events_by_lead
from app.crud.communication import create_communication, list_communications_by_lead
from app.crud.lead import create_lead, get_lead, list_leads, update_lead
from app.crud.tracking_event import get_first_click_event
from app.crud.user import get_user
from app.database import get_db
from app.models.affiliate_event import AffiliateEvent
from app.models.communication import Communication
from app.models.enums import CommunicationChannel, CommunicationDirection, UserRole
from app.models.task import Task
from app.models.tracking_event import TrackingEvent
from app.models.user import User
from app.schemas.affiliate_event import AffiliateEventOut
from app.schemas.communication import CommunicationListResponse, CommunicationOut, CommunicationSendRequest
from app.schemas.lead import (
    AcquisitionInfo,
    LeadAssign,
    LeadCardOut,
    LeadCreate,
    LeadListResponse,
    LeadOut,
    LeadUpdate,
    ManagerSummary,
)
from app.services.audit import write_audit_log
from app.services.auto_assignment import try_auto_assign
from app.services.chatterfy_client import ChatterfyClient, ChatterfySendError, get_chatterfy_client

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
    unassigned: bool = Query(default=False, description="Только неназначенные лиды (очередь unassigned)"),
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

    if unassigned and current_user.role not in CAN_ASSIGN_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    leads = await list_leads(
        db,
        cursor=decoded_cursor,
        limit=limit + 1,
        manager_id=manager_filter,
        geo=geo,
        status=status_filter,
        unassigned_only=unassigned,
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

    assigned_manager = await try_auto_assign(db, lead)
    if assigned_manager is not None:
        await write_audit_log(
            db,
            actor_id=None,
            action="manager_auto_assigned",
            entity_type="lead",
            entity_id=str(lead.lead_id),
            meta={"manager_id": str(assigned_manager.id)},
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

    # Если поменялись geo/dialect, а лид всё ещё не назначен - пробуем auto-assign повторно.
    if ("geo" in payload.model_fields_set or "dialect" in payload.model_fields_set) and (
        lead.assigned_manager_id is None
    ):
        assigned_manager = await try_auto_assign(db, lead)
        if assigned_manager is not None:
            await write_audit_log(
                db,
                actor_id=None,
                action="manager_auto_assigned",
                entity_type="lead",
                entity_id=str(lead.lead_id),
                meta={"manager_id": str(assigned_manager.id)},
            )

    await db.commit()
    return LeadOut.model_validate(lead)


@router.get("/{lead_id}/card", response_model=LeadCardOut)
async def get_lead_card_endpoint(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadCardOut:
    """Карточка лида: профиль, acquisition, менеджер, communication, affiliate (DoD Sprint 2)."""
    lead = await _get_lead_or_404(db, lead_id)
    _assert_can_view(current_user, lead)

    first_click = await get_first_click_event(db, lead_id)
    acquisition = AcquisitionInfo(
        source_channel=lead.source_channel,
        click_id=first_click.click_id if first_click else lead.external_click_id,
        campaign_id=first_click.campaign_id if first_click else None,
        adset_id=first_click.adset_id if first_click else None,
        creative_id=first_click.creative_id if first_click else None,
        landing_id=first_click.landing_id if first_click else None,
        first_seen_at=first_click.event_timestamp if first_click else lead.created_at,
    )

    manager = None
    if lead.assigned_manager_id is not None:
        manager_user = await get_user(db, lead.assigned_manager_id)
        if manager_user is not None:
            manager = ManagerSummary.model_validate(manager_user)

    communications = await list_communications_by_lead(db, lead_id)
    affiliate_events = await list_affiliate_events_by_lead(db, lead_id)

    return LeadCardOut(
        profile=LeadOut.model_validate(lead),
        acquisition=acquisition,
        manager=manager,
        communications=[CommunicationOut.model_validate(c) for c in communications],
        affiliate=[AffiliateEventOut.model_validate(e) for e in affiliate_events],
    )


@router.get("/{lead_id}/communications", response_model=CommunicationListResponse)
async def list_lead_communications_endpoint(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommunicationListResponse:
    lead = await _get_lead_or_404(db, lead_id)
    _assert_can_view(current_user, lead)

    communications = await list_communications_by_lead(db, lead_id)
    return CommunicationListResponse(items=[CommunicationOut.model_validate(c) for c in communications])


@router.post("/{lead_id}/communications", response_model=CommunicationOut, status_code=status.HTTP_201_CREATED)
async def send_lead_communication_endpoint(
    lead_id: uuid.UUID,
    payload: CommunicationSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chatterfy_client: ChatterfyClient = Depends(get_chatterfy_client),
) -> CommunicationOut:
    """Отправка исходящего сообщения лиду через Chatterfy (webhook out)."""
    lead = await _get_lead_or_404(db, lead_id)
    _assert_can_edit(current_user, lead)

    if not lead.telegram_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead has no linked telegram_user_id yet - cannot send a message",
        )

    communication = await create_communication(
        db,
        lead_id=lead.lead_id,
        manager_id=current_user.id,
        channel=CommunicationChannel.telegram,
        direction=CommunicationDirection.outbound,
        message_text=payload.message_text,
    )

    delivery_error: str | None = None
    try:
        await chatterfy_client.send_message(telegram_user_id=lead.telegram_user_id, text=payload.message_text)
    except ChatterfySendError as exc:
        delivery_error = str(exc)

    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="communication_sent",
        entity_type="lead",
        entity_id=str(lead.lead_id),
        meta={"communication_id": str(communication.id), "delivery_error": delivery_error},
    )
    await db.commit()
    return CommunicationOut.model_validate(communication)


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


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead_endpoint(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_DELETE_RECORDS)),
) -> None:
    """Жёсткое удаление лида (только admin). Communications/tasks удаляются
    вместе с лидом (без него бессмысленны); tracking_events/affiliate_events -
    исторические события с реальными деньгами/статистикой - НЕ удаляются,
    просто отвязываются (lead_id -> NULL), чтобы не терять аудиторский след."""
    lead = await _get_lead_or_404(db, lead_id)

    await db.execute(delete(Communication).where(Communication.lead_id == lead_id))
    await db.execute(delete(Task).where(Task.lead_id == lead_id))
    await db.execute(update(TrackingEvent).where(TrackingEvent.lead_id == lead_id).values(lead_id=None))
    await db.execute(update(AffiliateEvent).where(AffiliateEvent.lead_id == lead_id).values(lead_id=None))

    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="lead_deleted",
        entity_type="lead",
        entity_id=str(lead_id),
        meta={"geo": lead.geo, "status": lead.status.value},
    )

    await db.delete(lead)
    await db.commit()
