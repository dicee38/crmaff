from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_for_2fa_setup
from app.core.security import create_access_token, verify_password
from app.core.totp import generate_totp_secret, provisioning_uri, verify_totp_code
from app.crud.user import get_user_by_email
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UserOut,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")

    # 2FA обязательна для роли admin (нефункциональное требование).
    if user.role == UserRole.admin:
        if not user.is_2fa_enabled or not user.totp_secret:
            # Bootstrap: выдаём ограниченный токен (scope=2fa_setup), которым
            # можно вызвать ТОЛЬКО /auth/2fa/setup и /auth/2fa/verify - иначе
            # admin физически не смог бы включить 2FA при первом входе
            # (get_current_user такой токен никуда больше не пропустит).
            setup_token = create_access_token(
                subject=user.id, role=user.role.value, expires_minutes=15, scope="2fa_setup"
            )
            return TokenResponse(access_token=setup_token)
        if not payload.totp_code or not verify_totp_code(user.totp_secret, payload.totp_code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing 2FA code")

    access_token = create_access_token(subject=user.id, role=user.role.value)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user_for_2fa_setup),
    db: AsyncSession = Depends(get_db),
) -> TwoFactorSetupResponse:
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    current_user.is_2fa_enabled = False
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="2fa_setup_started",
        entity_type="user",
        entity_id=str(current_user.id),
        meta=None,
    )
    await db.commit()
    return TwoFactorSetupResponse(secret=secret, provisioning_uri=provisioning_uri(secret, current_user.email))


@router.post("/2fa/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_2fa(
    payload: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user_for_2fa_setup),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not current_user.totp_secret or not verify_totp_code(current_user.totp_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")
    current_user.is_2fa_enabled = True
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="2fa_enabled",
        entity_type="user",
        entity_id=str(current_user.id),
        meta=None,
    )
    await db.commit()
