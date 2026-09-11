import base64
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.rbac import CAN_DELETE_RECORDS, CAN_ENTER_MANUAL_ACTION, CAN_VIEW_ALL_ACTIONS
from app.crud.affiliate_event import (
    get_affiliate_event,
    aggregate_affiliate_events,
    create_affiliate_event,
    find_possible_duplicate,
    list_affiliate_events,
)
from app.crud.lead import (
    get_lead_by_external_click_id,
    get_lead_by_telegram_user_id,
    get_leads_by_ids,
    list_lead_ids_by_manager,
)
from app.crud.user import get_users_by_ids
from app.database import get_db
from app.models.affiliate_event import AffiliateEvent
from app.models.enums import AffiliateEventSource, AffiliateEventType
from app.models.user import User
from app.schemas.action import AMOUNT_REQUIRED_TYPES, ActionListResponse, ActionRow, ManualActionCreate
from app.schemas.affiliate_event import AffiliateEventOut
from app.services.audit import write_audit_log

router = APIRouter(prefix="/actions", tags=["actions"])


def _encode_cursor(dt: datetime) -> str:
    return base64.urlsafe_b64encode(dt.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    try:
        return datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor") from exc


def _player_external_id(event: AffiliateEvent) -> str | None:
    """ID игрока для отображения: uid от Binolla-постбэка или player_id,
    введённый вручную - см. normalized_payload в webhooks.py / actions.py."""
    payload = event.normalized_payload or {}
    return payload.get("trader_id") or payload.get("player_id")


async def _build_action_rows(db: AsyncSession, events: list[AffiliateEvent]) -> list[ActionRow]:
    lead_ids = {e.lead_id for e in events if e.lead_id is not None}
    leads_by_id = await get_leads_by_ids(db, list(lead_ids))

    manager_ids = {
        lead.assigned_manager_id for lead in leads_by_id.values() if lead.assigned_manager_id is not None
    }
    managers_by_id = await get_users_by_ids(db, list(manager_ids))

    rows = []
    for event in events:
        lead = leads_by_id.get(event.lead_id) if event.lead_id else None
        manager = managers_by_id.get(lead.assigned_manager_id) if lead and lead.assigned_manager_id else None
        rows.append(
            ActionRow(
                id=event.id,
                received_at=event.received_at,
                partner=event.partner,
                channel=event.channel,
                event_type=event.event_type,
                source=event.source,
                player_external_id=_player_external_id(event),
                amount=event.amount,
                currency=event.currency,
                lead_id=event.lead_id,
                manager_full_name=manager.full_name if manager else None,
                manager_role=manager.role.value if manager else None,
                validation_flags=event.validation_flags,
            )
        )
    return rows


@router.post("", response_model=AffiliateEventOut, status_code=status.HTTP_201_CREATED)
async def create_manual_action_endpoint(
    payload: ManualActionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_ENTER_MANUAL_ACTION)),
) -> AffiliateEventOut:
    if payload.event_type in AMOUNT_REQUIRED_TYPES and payload.amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"amount is required for event_type={payload.event_type}",
        )

    lead = await get_lead_by_external_click_id(db, payload.player_id)
    if lead is None:
        lead = await get_lead_by_telegram_user_id(db, payload.player_id)

    occurred_at = payload.occurred_at or datetime.now(timezone.utc)

    validation_flags: dict = {}
    if lead is None:
        validation_flags["unmatched_lead"] = True
    else:
        duplicate = await find_possible_duplicate(
            db,
            lead_id=lead.lead_id,
            event_type=AffiliateEventType(payload.event_type),
            amount=payload.amount,
            occurred_on=occurred_at.date(),
        )
        if duplicate is not None:
            validation_flags["possible_duplicate"] = True

    event = await create_affiliate_event(
        db,
        lead_id=lead.lead_id if lead else None,
        partner=payload.partner_name,
        external_event_id=f"manual:{uuid.uuid4()}",
        event_type=AffiliateEventType(payload.event_type),
        source=AffiliateEventSource.manual,
        entered_by=current_user.id,
        channel=payload.channel,
        amount=payload.amount,
        currency=payload.currency,
        raw_payload=payload.model_dump(mode="json"),
        normalized_payload={"player_id": payload.player_id, "matched_lead_id": str(lead.lead_id) if lead else None},
        validation_flags=validation_flags or None,
        received_at=occurred_at,
    )

    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="manual_action_entered",
        entity_type="affiliate_event",
        entity_id=str(event.id),
        meta={
            "lead_id": str(lead.lead_id) if lead else None,
            "event_type": payload.event_type,
            "validation_flags": validation_flags,
        },
    )
    await db.commit()
    return AffiliateEventOut.model_validate(event)


@router.get("", response_model=ActionListResponse)
async def list_actions_endpoint(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    event_id: uuid.UUID | None = Query(default=None),
    lead_id: uuid.UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    source: str | None = Query(default=None, description="all|api|manual"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    amount_min: Decimal | None = Query(default=None),
    amount_max: Decimal | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionListResponse:
    if current_user.role not in CAN_VIEW_ALL_ACTIONS and current_user.role not in CAN_ENTER_MANUAL_ACTION:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    decoded_cursor = _decode_cursor(cursor) if cursor else None

    manager_lead_ids = None
    if current_user.role not in CAN_VIEW_ALL_ACTIONS:
        # sales_manager (и любая другая роль с доступом только к своему) видит
        # действия только по своим лидам.
        manager_lead_ids = await list_lead_ids_by_manager(db, current_user.id)

    source_filter = None
    if source == "api":
        source_filter = AffiliateEventSource.postback
    elif source == "manual":
        source_filter = AffiliateEventSource.manual

    filters = dict(
        manager_lead_ids=manager_lead_ids,
        event_id=event_id,
        lead_id=lead_id,
        event_type=event_type,
        source=source_filter,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
    )

    events = await list_affiliate_events(db, cursor=decoded_cursor, limit=limit + 1, **filters)
    next_cursor = None
    if len(events) > limit:
        events = events[:limit]
        next_cursor = _encode_cursor(events[-1].received_at)

    aggregates = await aggregate_affiliate_events(db, **filters)

    return ActionListResponse(
        items=await _build_action_rows(db, events),
        next_cursor=next_cursor,
        aggregates=aggregates,
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_endpoint(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_DELETE_RECORDS)),
) -> None:
    """Жёсткое удаление записи действия (postback или manual) - только admin."""
    event = await get_affiliate_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="affiliate_event_deleted",
        entity_type="affiliate_event",
        entity_id=str(event_id),
        meta={
            "external_event_id": event.external_event_id,
            "event_type": event.event_type.value,
            "lead_id": str(event.lead_id) if event.lead_id else None,
        },
    )

    await db.delete(event)
    await db.commit()
