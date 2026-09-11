import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.rbac import CAN_MANAGE_REFERENCE_DATA
from app.crud.channel import create_channel, get_channel, get_channel_by_name, list_channels
from app.crud.partner import create_partner, get_partner, get_partner_by_name, list_partners
from app.database import get_db
from app.models.user import User
from app.schemas.reference import (
    ActiveToggle,
    ChannelCreate,
    ChannelOut,
    PartnerCreate,
    PartnerOut,
)
from app.services.audit import write_audit_log

router = APIRouter(tags=["reference"])


@router.get("/partners", response_model=list[PartnerOut])
async def list_partners_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PartnerOut]:
    partners = await list_partners(db)
    return [PartnerOut.model_validate(p) for p in partners]


@router.post("/partners", response_model=PartnerOut, status_code=status.HTTP_201_CREATED)
async def create_partner_endpoint(
    payload: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_MANAGE_REFERENCE_DATA)),
) -> PartnerOut:
    existing = await get_partner_by_name(db, payload.name)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Partner already exists")
    partner = await create_partner(db, name=payload.name)
    await write_audit_log(
        db, actor_id=current_user.id, action="partner_created", entity_type="partner", entity_id=str(partner.id)
    )
    await db.commit()
    return PartnerOut.model_validate(partner)


@router.patch("/partners/{partner_id}", response_model=PartnerOut)
async def update_partner_endpoint(
    partner_id: uuid.UUID,
    payload: ActiveToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_MANAGE_REFERENCE_DATA)),
) -> PartnerOut:
    partner = await get_partner(db, partner_id)
    if partner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    partner.is_active = payload.is_active
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="partner_updated",
        entity_type="partner",
        entity_id=str(partner.id),
        meta={"is_active": payload.is_active},
    )
    await db.commit()
    return PartnerOut.model_validate(partner)


@router.get("/channels", response_model=list[ChannelOut])
async def list_channels_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChannelOut]:
    channels = await list_channels(db)
    return [ChannelOut.model_validate(c) for c in channels]


@router.post("/channels", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
async def create_channel_endpoint(
    payload: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_MANAGE_REFERENCE_DATA)),
) -> ChannelOut:
    existing = await get_channel_by_name(db, payload.name)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Channel already exists")
    channel = await create_channel(db, name=payload.name)
    await write_audit_log(
        db, actor_id=current_user.id, action="channel_created", entity_type="channel", entity_id=str(channel.id)
    )
    await db.commit()
    return ChannelOut.model_validate(channel)


@router.patch("/channels/{channel_id}", response_model=ChannelOut)
async def update_channel_endpoint(
    channel_id: uuid.UUID,
    payload: ActiveToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CAN_MANAGE_REFERENCE_DATA)),
) -> ChannelOut:
    channel = await get_channel(db, channel_id)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    channel.is_active = payload.is_active
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="channel_updated",
        entity_type="channel",
        entity_id=str(channel.id),
        meta={"is_active": payload.is_active},
    )
    await db.commit()
    return ChannelOut.model_validate(channel)
