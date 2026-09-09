from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.config import get_settings

settings = get_settings()

engine_kwargs: dict = {"echo": False}
if settings.database_url.startswith("sqlite"):
    # Используется только в тестах (SQLite in-memory) - продакшн всегда на Postgres 15+.
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    if ":memory:" in settings.database_url:
        engine_kwargs["poolclass"] = StaticPool
else:
    # Дефолтный QueuePool (5 + 10 overflow = 15) слишком мал под конкурентную
    # нагрузку и даёт P95 > 300ms на карточке лида уже при concurrency=20
    # (см. scripts/run_load_test.py) - запросы простаивают в очереди на
    # соединение, а не выполняются медленно. NFR: P95 < 300ms.
    engine_kwargs["pool_size"] = 40
    engine_kwargs["max_overflow"] = 40
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.database_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
