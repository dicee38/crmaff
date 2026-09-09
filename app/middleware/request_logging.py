"""Структурированный access-log вместо дефолтного uvicorn access-log.

Дефолтный access-log uvicorn пишет ПОЛНУЮ query-строку без редактирования -
для /webhooks/binolla это означает секрет (?secret=...) в открытом виде в
каждой строке лога. Логи обычно уезжают в агрегаторы с более широким
доступом, чем к самой БД/коду - секрет там светиться не должен (тот же
принцип, что "Секреты - только через env/secret manager", NFR CLAUDE.md).

Uvicorn запускается с --no-access-log (см. Dockerfile/docker-compose.yml),
эта миддлварь - единственный источник access-логов.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import get_logger

logger = get_logger("access")

# Query-параметры, значения которых никогда не должны попадать в логи целиком.
_REDACT_PARAMS = {"secret", "token", "signature", "code", "password"}


def _redacted_query(request: Request) -> str:
    if not request.query_params:
        return ""
    parts = []
    for key, value in request.query_params.multi_items():
        if key.lower() in _REDACT_PARAMS:
            value = "***"
        parts.append(f"{key}={value}")
    return "&".join(parts)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            query=_redacted_query(request),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            client_ip=request.client.host if request.client else None,
        )
        return response
