import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def _resolve_user_from_token(
    token: str | None, db: AsyncSession
) -> tuple[User, dict]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception

    return user, payload


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Обычная аутентификация - требует полноценный токен (scope=full).

    Токен с scope=2fa_setup (выданный при первом логине admin без включённой
    2FA) сюда не проходит - им можно вызвать только /auth/2fa/setup и
    /auth/2fa/verify, см. get_current_user_for_2fa_setup ниже.
    """
    user, payload = await _resolve_user_from_token(token, db)
    if payload.get("scope", "full") != "full":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA setup required before this action is allowed",
        )
    return user


async def get_current_user_for_2fa_setup(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Принимает и полноценный токен, и bootstrap-токен scope=2fa_setup -
    используется только эндпоинтами /auth/2fa/setup и /auth/2fa/verify,
    чтобы admin мог включить 2FA при первом входе (до этого get_current_user
    его токен не пропустит никуда больше)."""
    user, _payload = await _resolve_user_from_token(token, db)
    return user


def require_roles(*roles: UserRole) -> Callable:
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
        return current_user

    return _checker
