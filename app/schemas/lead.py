import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ConsentStatus, Dialect, LeadStatus, SourceChannel


class LeadCreate(BaseModel):
    external_click_id: str | None = None
    geo: str | None = None
    language: str | None = None
    dialect: Dialect | None = None
    source_channel: SourceChannel = SourceChannel.organic
    telegram_user_id: str | None = None
    offer_id: uuid.UUID | None = None
    consent_status: ConsentStatus = ConsentStatus.unknown


class LeadUpdate(BaseModel):
    geo: str | None = None
    language: str | None = None
    dialect: Dialect | None = None
    status: LeadStatus | None = None
    assigned_manager_id: uuid.UUID | None = None
    offer_id: uuid.UUID | None = None
    consent_status: ConsentStatus | None = None


class LeadAssign(BaseModel):
    manager_id: uuid.UUID


class LeadOut(BaseModel):
    lead_id: uuid.UUID
    external_click_id: str | None
    geo: str | None
    language: str | None
    dialect: Dialect | None
    source_channel: SourceChannel
    status: LeadStatus
    assigned_manager_id: uuid.UUID | None
    offer_id: uuid.UUID | None
    telegram_user_id: str | None
    consent_status: ConsentStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    items: list[LeadOut]
    next_cursor: str | None = Field(default=None, description="Курсор для следующей страницы")
