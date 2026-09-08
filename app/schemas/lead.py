import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ConsentStatus, Dialect, LeadStatus, SourceChannel
from app.schemas.affiliate_event import AffiliateEventOut
from app.schemas.communication import CommunicationOut


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


class ManagerSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class AcquisitionInfo(BaseModel):
    source_channel: SourceChannel
    click_id: str | None
    campaign_id: str | None
    adset_id: str | None
    creative_id: str | None
    landing_id: str | None
    first_seen_at: datetime | None


class LeadCardOut(BaseModel):
    """Карточка лида: все 5 блоков (DoD Sprint 2)."""

    profile: LeadOut
    acquisition: AcquisitionInfo | None
    manager: ManagerSummary | None
    communications: list[CommunicationOut]
    affiliate: list[AffiliateEventOut]
