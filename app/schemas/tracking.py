import uuid
from datetime import datetime

from pydantic import BaseModel


class TrackClickRequest(BaseModel):
    click_id: str
    session_id: str | None = None
    campaign_id: str | None = None
    adset_id: str | None = None
    creative_id: str | None = None
    landing_id: str | None = None
    geo: str | None = None
    language: str | None = None
    telegram_user_id: str | None = None
    external_click_id: str | None = None


class TrackClickResponse(BaseModel):
    lead_id: uuid.UUID
    tracking_event_id: uuid.UUID
    click_id: str
    created_at: datetime
