from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.signing import verify_hmac_signature, verify_shared_secret
from app.crud.affiliate_event import create_affiliate_event, get_affiliate_event_by_external_id
from app.crud.communication import create_communication, get_communication_by_external_message_id
from app.crud.lead import get_lead_by_external_click_id, update_lead
from app.database import get_db
from app.logging_config import get_logger
from app.models.enums import AffiliateEventType, CommunicationChannel, CommunicationDirection, LeadStatus
from app.schemas.binolla import STATUS_TO_EVENT_TYPE, BinollaWebhookResponse
from app.schemas.chatterfy import ChatterfyInboundMessage, ChatterfyWebhookResponse
from app.schemas.lead import LeadUpdate
from app.services.audit import write_audit_log
from app.services.lead_id import resolve_or_create_lead_for_message
from app.services.lead_status import BINOLLA_EVENT_TO_LEAD_STATUS, is_forward_transition

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = get_logger(__name__)
settings = get_settings()


@router.post("/chatterfy", response_model=ChatterfyWebhookResponse)
async def chatterfy_webhook(
    payload: ChatterfyInboundMessage,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ChatterfyWebhookResponse:
    # 1. Проверить подпись.
    signature = request.headers.get("X-Signature")
    raw_body = await request.body()
    if not verify_hmac_signature(settings.chatterfy_webhook_secret, raw_body, signature):
        logger.warning("chatterfy_webhook.invalid_signature", external_message_id=payload.external_message_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # 2. Payload уже провалидирован Pydantic-схемой.

    # 3. Идемпотентность по external_message_id - при повторе вернуть 200 без повторной обработки.
    existing = await get_communication_by_external_message_id(db, payload.external_message_id)
    if existing is not None:
        return ChatterfyWebhookResponse(lead_id=existing.lead_id, communication_id=existing.id)

    # 4. Определить lead_id (создаёт лид при первом сообщении, сопоставляет по click_id/telegram_user_id).
    resolution = await resolve_or_create_lead_for_message(
        db,
        telegram_user_id=payload.telegram_user_id,
        click_id=payload.start_param,
    )
    lead = resolution.lead

    # 5-6. raw_payload сохраняется как есть в communications через message_text/поля;
    # нормализованное сообщение - сама схема ChatterfyInboundMessage.
    communication = await create_communication(
        db,
        lead_id=lead.lead_id,
        manager_id=None,
        channel=CommunicationChannel.telegram,
        direction=CommunicationDirection.inbound,
        message_text=payload.message_text,
        external_message_id=payload.external_message_id,
    )

    # 7. Обновить статус лида, если применимо: new -> contacted при первом входящем сообщении.
    if lead.status == LeadStatus.new:
        await update_lead(db, lead, LeadUpdate(status=LeadStatus.contacted))

    # 8. audit_log.
    await write_audit_log(
        db,
        actor_id=None,
        action="lead_created_via_chatterfy" if resolution.is_new else "chatterfy_message_received",
        entity_type="lead",
        entity_id=str(lead.lead_id),
        meta={"external_message_id": payload.external_message_id, "communication_id": str(communication.id)},
    )

    await db.commit()

    # 9. Корректный HTTP-код (2xx).
    return ChatterfyWebhookResponse(lead_id=lead.lead_id, communication_id=communication.id)


@router.get("/binolla", response_model=BinollaWebhookResponse)
async def binolla_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BinollaWebhookResponse:
    params = request.query_params

    # 1. Проверить секрет (GET без тела - HMAC-подпись неприменима, секрет в query).
    if not verify_shared_secret(settings.binolla_webhook_secret, params.get("secret")):
        logger.warning("binolla_webhook.invalid_secret")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret")

    # 2. Провалидировать структуру payload.
    event_status = params.get("status")
    external_event_id = params.get("eid")
    click_id = params.get("cid")
    if not event_status or not external_event_id or not click_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields")

    event_type_value = STATUS_TO_EVENT_TYPE.get(event_status)
    if event_type_value is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown status: {event_status}")
    event_type = AffiliateEventType(event_type_value)

    # 5. raw_payload сохраняется как есть, до любой трансформации.
    raw_payload = dict(params)

    # 3. Идемпотентность по eid - при повторе вернуть 200 без повторной обработки.
    existing = await get_affiliate_event_by_external_id(db, external_event_id)
    if existing is not None:
        return BinollaWebhookResponse(
            lead_id=existing.lead_id,
            affiliate_event_id=existing.id,
            unmatched=existing.lead_id is None,
        )

    # 4. Определить lead_id по click_id (cid).
    lead = await get_lead_by_external_click_id(db, click_id)

    # 6. Нормализация: payout -> Decimal (пусто/нет для нефинансовых событий).
    amount: Decimal | None = None
    payout_raw = params.get("payout")
    if payout_raw:
        try:
            amount = Decimal(payout_raw)
        except InvalidOperation:
            amount = None

    validation_flags: dict | None = None
    if lead is None:
        # Неизвестный lead_id - НЕ отбрасываем событие, помечаем на эскалацию Affiliate Manager.
        validation_flags = {"unmatched_lead": True}

    affiliate_event = await create_affiliate_event(
        db,
        lead_id=lead.lead_id if lead else None,
        partner="binolla",
        external_event_id=external_event_id,
        event_type=event_type,
        amount=amount,
        currency="USD" if amount is not None else None,
        raw_payload=raw_payload,
        normalized_payload={
            "event_type": event_type.value,
            "click_id": click_id,
            "trader_id": params.get("uid"),
            "site_id": params.get("sid"),
            "link_id": params.get("lid"),
            "amount": str(amount) if amount is not None else None,
        },
        validation_flags=validation_flags,
    )

    # 7. Обновить статус лида, если применимо (только вперёд по воронке).
    if lead is not None:
        target_status = BINOLLA_EVENT_TO_LEAD_STATUS.get(event_type.value)
        if target_status is not None and is_forward_transition(lead.status, target_status):
            await update_lead(db, lead, LeadUpdate(status=target_status))

    # 8. audit_log.
    await write_audit_log(
        db,
        actor_id=None,
        action="affiliate_event_unmatched" if lead is None else "affiliate_event_received",
        entity_type="lead",
        entity_id=str(lead.lead_id) if lead else click_id,
        meta={
            "external_event_id": external_event_id,
            "affiliate_event_id": str(affiliate_event.id),
            "event_type": event_type.value,
        },
    )

    await db.commit()

    # 9. Корректный HTTP-код (2xx, событие принято и сохранено даже если lead не сматчен).
    return BinollaWebhookResponse(
        lead_id=lead.lead_id if lead else None,
        affiliate_event_id=affiliate_event.id,
        unmatched=lead is None,
    )
