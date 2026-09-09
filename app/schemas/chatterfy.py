"""Нормализованный внутренний контракт для интеграции с Chatterfy.

⚠️ Точные поля/заголовки реального Chatterfy webhook нужно сверить с их
актуальной документацией перед продакшн-использованием (см. CLAUDE.md) -
здесь описан наш внутренний нормализованный формат.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ChatterfyInboundMessage(BaseModel):
    external_message_id: str
    telegram_user_id: str
    chat_id: str | None = None
    message_text: str | None = None
    start_param: str | None = None  # deep-link /start параметр бота = click_id
    sent_at: datetime | None = None


class ChatterfyWebhookResponse(BaseModel):
    status: str = "ok"
    lead_id: uuid.UUID | None = None
    communication_id: uuid.UUID | None = None
