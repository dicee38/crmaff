from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import RateLimiter
from app.core.signing import verify_hmac_signature
from app.crud.tracking_event import create_tracking_event
from app.database import get_db
from app.logging_config import get_logger
from app.models.enums import TrackingEventType
from app.models.tracking_event import TrackingEvent
from app.schemas.tracking import TrackClickRequest, TrackClickResponse
from app.services.audit import write_audit_log
from app.services.lead_id import resolve_or_create_lead_for_click

router = APIRouter(prefix="/track", tags=["tracking"])
logger = get_logger(__name__)
settings = get_settings()


@router.post("/click", response_model=TrackClickResponse, dependencies=[Depends(RateLimiter())])
async def track_click(
    payload: TrackClickRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TrackClickResponse:
    # 1. Проверить подпись.
    signature = request.headers.get("X-Signature")
    raw_body = await request.body()
    if not verify_hmac_signature(settings.track_click_signing_secret, raw_body, signature):
        logger.warning("track_click.invalid_signature", click_id=payload.click_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # 2. Payload уже провалидирован Pydantic-схемой.

    # 3. Идемпотентность: повторный клик с тем же click_id -> вернуть существующее событие.
    existing_event_result = await db.execute(
        select(TrackingEvent).where(
            TrackingEvent.click_id == payload.click_id,
            TrackingEvent.event_type == TrackingEventType.click,
        )
    )
    existing_event = existing_event_result.scalar_one_or_none()
    if existing_event is not None:
        return TrackClickResponse(
            lead_id=existing_event.lead_id,
            tracking_event_id=existing_event.id,
            click_id=payload.click_id,
            created_at=existing_event.created_at,
        )

    # 4. Определить lead_id (создаёт лид при первом клике, не дублирует при повторных).
    resolution = await resolve_or_create_lead_for_click(
        db,
        click_id=payload.click_id,
        telegram_user_id=payload.telegram_user_id,
        geo=payload.geo,
        language=payload.language,
    )

    # 5-6. raw_payload сохраняется как есть, event_type=click.
    event = await create_tracking_event(
        db,
        lead_id=resolution.lead.lead_id,
        event_type=TrackingEventType.click,
        click_id=payload.click_id,
        session_id=payload.session_id,
        campaign_id=payload.campaign_id,
        adset_id=payload.adset_id,
        creative_id=payload.creative_id,
        landing_id=payload.landing_id,
        raw_payload=payload.model_dump(mode="json"),
    )

    # 8. audit_log на создание лида/события.
    await write_audit_log(
        db,
        actor_id=None,
        action="lead_created" if resolution.is_new else "click_recorded",
        entity_type="lead",
        entity_id=str(resolution.lead.lead_id),
        meta={"click_id": payload.click_id, "tracking_event_id": str(event.id)},
    )

    await db.commit()

    return TrackClickResponse(
        lead_id=resolution.lead.lead_id,
        tracking_event_id=event.id,
        click_id=payload.click_id,
        created_at=event.created_at,
    )
