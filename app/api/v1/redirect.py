"""Публичный click-редирект: пользователь кликает по рекламе -> мы логируем
клик и создаём/сопоставляем лид -> 302 на оффер партнёра с нашим click_id.

Без auth/подписи (реальный браузер пользователя не может подписать запрос) -
защищён только rate limiting (см. app/core/rate_limit.py), как того требует
NFR "Rate limiting на /track/click и публичных эндпоинтах".
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimiter
from app.crud.offer import get_offer
from app.crud.tracking_event import create_tracking_event
from app.database import get_db
from app.models.enums import OfferStatus, TrackingEventType
from app.services.audit import write_audit_log
from app.services.lead_id import resolve_or_create_lead_for_click

router = APIRouter(tags=["tracking"])


@router.get("/go/{offer_id}", dependencies=[Depends(RateLimiter())])
async def go_to_offer(
    offer_id: uuid.UUID,
    campaign_id: str | None = Query(default=None),
    adset_id: str | None = Query(default=None),
    creative_id: str | None = Query(default=None),
    landing_id: str | None = Query(default=None),
    geo: str | None = Query(default=None),
    language: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    offer = await get_offer(db, offer_id)
    if offer is None or offer.status != OfferStatus.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    if not offer.redirect_url_template:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Offer has no redirect configured")

    # click_id генерируется нами - это первая точка входа трафика, дальше он
    # проходит транзитом через партнёра и возвращается в postback (cid).
    click_id = uuid.uuid4().hex

    resolution = await resolve_or_create_lead_for_click(
        db,
        click_id=click_id,
        geo=geo,
        language=language,
    )

    event = await create_tracking_event(
        db,
        lead_id=resolution.lead.lead_id,
        event_type=TrackingEventType.click,
        click_id=click_id,
        campaign_id=campaign_id,
        adset_id=adset_id,
        creative_id=creative_id,
        landing_id=landing_id,
        raw_payload={
            "offer_id": str(offer_id),
            "campaign_id": campaign_id,
            "adset_id": adset_id,
            "creative_id": creative_id,
            "landing_id": landing_id,
            "geo": geo,
            "language": language,
        },
    )

    await write_audit_log(
        db,
        actor_id=None,
        action="lead_created" if resolution.is_new else "click_recorded",
        entity_type="lead",
        entity_id=str(resolution.lead.lead_id),
        meta={"click_id": click_id, "tracking_event_id": str(event.id), "offer_id": str(offer_id)},
    )

    await db.commit()

    redirect_url = offer.redirect_url_template.replace("{click_id}", click_id)
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
