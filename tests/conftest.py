import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["TRACK_CLICK_SIGNING_SECRET"] = "test-track-secret"
os.environ["CHATTERFY_WEBHOOK_SECRET"] = "test-chatterfy-secret"
os.environ["BINOLLA_WEBHOOK_SECRET"] = "test-binolla-secret"
os.environ["REDIS_URL"] = "redis://localhost:65530/0"  # заведомо недоступен - проверяем fail-open rate limiter

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.crud.user import create_user
from app.database import AsyncSessionLocal, Base, engine, get_db
from app.main import app
from app.models.enums import UserRole


@pytest_asyncio.fixture(autouse=True)
async def _prepare_database() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def make_user(db_session, role: UserRole, **kwargs):
    return await create_user(
        db_session,
        full_name=kwargs.get("full_name", f"Test {role.value}"),
        email=kwargs.get("email", f"{role.value}-{uuid.uuid4().hex[:8]}@example.com"),
        password=kwargs.get("password", "password123"),
        role=role,
        geo_coverage=kwargs.get("geo_coverage", []),
        dialects=kwargs.get("dialects", []),
    )


def auth_headers(user) -> dict:
    token = create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}
