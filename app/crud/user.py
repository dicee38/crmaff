import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    full_name: str,
    email: str,
    password: str,
    role: UserRole,
    geo_coverage: list[str] | None = None,
    dialects: list[str] | None = None,
) -> User:
    user = User(
        id=uuid.uuid4(),
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        geo_coverage=geo_coverage or [],
        dialects=dialects or [],
    )
    db.add(user)
    await db.flush()
    return user
