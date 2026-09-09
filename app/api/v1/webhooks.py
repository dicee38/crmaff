from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.signing import verify_hmac_signature
from app.crud.communication import create_communication, get_communication_by_external_message_id
from app.crud.lead import update_lead
from app.database import get_db
from app.logging_config import get_logger
from app.models.enums import CommunicationChannel, CommunicationDirection, LeadStatus
from app.schemas.chatterfy import ChatterfyInboundMessage, ChatterfyWebhookResponse
from app.schemas.lead import LeadUpdate
from app.services.audit import write_audit_log
from app.services.lead_id import resolve_or_create_lead_for_message

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
