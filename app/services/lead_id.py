"""Lead ID resolution pipeline.

Правила (см. CLAUDE.md, раздел "Lead ID — правила"):
1. UUID v4, генерируется только на backend.
2. Создаётся при первом связанном событии: клик ИЛИ первое входящее сообщение
   в Chatterfy без предшествующего клика.
3. Клик -> потом сообщение в Telegram сопоставляется по click_id
   (deep-link/start-параметр бота).
4. Если сопоставить не удалось - новый lead_id, source_channel = organic.
5. НЕ пересоздавать lead_id для одного и того же пользователя - искать сначала
   по telegram_user_id / external_click_id.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.lead import create_lead, get_lead_by_external_click_id, get_lead_by_telegram_user_id
from app.models.enums import ConsentStatus, Dialect, SourceChannel
from app.models.lead import Lead
from app.schemas.lead import LeadCreate
from app.services.auto_assignment import try_auto_assign


@dataclass
class LeadResolution:
    lead: Lead
    is_new: bool


async def resolve_or_create_lead_for_click(
    db: AsyncSession,
    *,
    click_id: str,
    telegram_user_id: str | None = None,
    geo: str | None = None,
    language: str | None = None,
    dialect: Dialect | None = None,
) -> LeadResolution:
    """Резолвит lead_id для входящего клика.

    Сначала ищем существующий лид (правило 5), чтобы не плодить дубли при
    повторных кликах того же пользователя. Если не нашли - создаём новый
    лид с source_channel=telegram_ads и привязкой click_id.
    """
    existing: Lead | None = None
    if telegram_user_id:
        existing = await get_lead_by_telegram_user_id(db, telegram_user_id)
    if existing is None:
        existing = await get_lead_by_external_click_id(db, click_id)

    if existing is not None:
        return LeadResolution(lead=existing, is_new=False)

    lead = await create_lead(
        db,
        LeadCreate(
            external_click_id=click_id,
            geo=geo,
            language=language,
            dialect=dialect,
            source_channel=SourceChannel.telegram_ads,
            telegram_user_id=telegram_user_id,
            consent_status=ConsentStatus.unknown,
        ),
    )
    await try_auto_assign(db, lead)
    return LeadResolution(lead=lead, is_new=True)


async def resolve_or_create_lead_for_message(
    db: AsyncSession,
    *,
    telegram_user_id: str,
    click_id: str | None = None,
) -> LeadResolution:
    """Резолвит lead_id для входящего сообщения Chatterfy.

    Правило 5: сначала ищем по telegram_user_id (не пересоздаём лид для
    уже знакомого пользователя). Правило 3: если лида ещё нет, но в
    сообщении пришёл click_id (deep-link/start-параметр бота) -
    сопоставляем с лидом, созданным по клику, и дозаполняем
    telegram_user_id. Правило 4: если сопоставить не удалось - новый лид,
    source_channel=organic.
    """
    existing = await get_lead_by_telegram_user_id(db, telegram_user_id)
    if existing is not None:
        return LeadResolution(lead=existing, is_new=False)

    if click_id:
        existing = await get_lead_by_external_click_id(db, click_id)
        if existing is not None:
            existing.telegram_user_id = telegram_user_id
            await db.flush()
            return LeadResolution(lead=existing, is_new=False)

    lead = await create_lead(
        db,
        LeadCreate(
            external_click_id=click_id,
            source_channel=SourceChannel.organic,
            telegram_user_id=telegram_user_id,
            consent_status=ConsentStatus.unknown,
        ),
    )
    await try_auto_assign(db, lead)
    return LeadResolution(lead=lead, is_new=True)
