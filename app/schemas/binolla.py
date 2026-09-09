"""Нормализованный контракт постбэка Binolla.

⚠️ Основано на скриншоте конфигурации постбэка партнёра (Postback format:
`?status={status}&{status}=true&eid={event_id}&cid={click_id}&sid={site_id}
&lid={lid}&uid={trader_id}&payout={sumdep}`, метод GET). Сверить с реальной
доставкой перед продакшн-использованием - см. CLAUDE.md.
"""

import uuid

from pydantic import BaseModel

# status -> наш внутренний AffiliateEventType
STATUS_TO_EVENT_TYPE = {
    "reg": "registration",
    "conf": "email_confirmed",
    "ftd": "ftd",
    "dep": "deposit",
}


class BinollaWebhookResponse(BaseModel):
    status: str = "ok"
    lead_id: uuid.UUID | None = None
    affiliate_event_id: uuid.UUID | None = None
    unmatched: bool = False
