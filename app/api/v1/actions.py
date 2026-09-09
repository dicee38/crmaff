import base64
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.rbac import CAN_ENTER_MANUAL_ACTION, CAN_VIEW_ALL_ACTIONS
from app.crud.affiliate_event import (
    aggregate_affiliate_events,
    create_affiliate_event,
    find_possible_duplicate,
    list_affiliate_events,
)
from app.crud.lead import get_lead_by_external_click_id, get_lead_by_telegram_user_id, list_lead_ids_by_manager
from app.database import get_db
from app.models.enums import AffiliateEventSource, AffiliateEventType
from app.models.user import User
from app.schemas.action import AMOUNT_REQUIRED_TYPES, ActionListResponse, ManualActionCreate
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
        items=[AffiliateEventOut.model_validate(e) for e in events],
        next_cursor=next_cursor,
        aggregates=aggregates,
    )
