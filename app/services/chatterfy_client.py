"""Клиент исходящих сообщений в Chatterfy.

⚠️ Точный контракт запроса (путь, поля, заголовки аутентификации) нужно
сверить с актуальной документацией Chatterfy перед продакшн-использованием
(см. CLAUDE.md) - это рабочая реализация поверх нормализованного контракта,
не финальная интеграция.

Отправка сообщения не должна ронять операцию CRM при недоступности партнёра:
ошибка логируется, запись в `communications` и `audit_logs` всё равно
сохраняется (менеджер увидит сообщение в истории, доставка - best-effort).
"""

import httpx

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class ChatterfySendError(Exception):
    pass


class ChatterfyClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.chatterfy_api_base_url
        self._api_key = settings.chatterfy_api_key

    async def send_message(self, *, telegram_user_id: str, text: str) -> None:
        if not self._base_url:
            logger.warning("chatterfy.send_message.not_configured", telegram_user_id=telegram_user_id)
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self._base_url}/messages",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={"telegram_user_id": telegram_user_id, "text": text},
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("chatterfy.send_message.failed", telegram_user_id=telegram_user_id, error=str(exc))
            raise ChatterfySendError(str(exc)) from exc


def get_chatterfy_client() -> ChatterfyClient:
    return ChatterfyClient()
