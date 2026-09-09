"""Rate limiting на публичных эндпоинтах (NFR из CLAUDE.md).

Fixed-window счётчик в Redis, ключ = путь + IP клиента. Fail-open: если
Redis недоступен, запрос пропускается, а не блокируется - инфраструктурный
сбой Redis не должен ронять публичный трафик (клики по рекламе, postback'и
партнёра). Инцидент логируется.
"""

from functools import lru_cache

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@lru_cache
def _get_redis_client() -> redis.Redis:
    # Короткие таймауты обязательны: fail-open должен быть быстрым, иначе
    # недоступный Redis не "мягко деградирует", а добавляет к каждому
    # публичному запросу задержку в секунды (дефолтный TCP connect timeout).
    return redis.from_url(
        get_settings().redis_url,
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=0.5,
    )


class RateLimiter:
    def __init__(self, times: int | None = None, seconds: int = 60) -> None:
        self.times = times if times is not None else get_settings().rate_limit_public_per_minute
        self.seconds = seconds

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{request.url.path}:{client_ip}"

        try:
            client = _get_redis_client()
            current = await client.incr(key)
            if current == 1:
                await client.expire(key, self.seconds)
        except (redis.RedisError, OSError) as exc:
            logger.warning("rate_limit.redis_unavailable", error=str(exc))
            return

        if current > self.times:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
