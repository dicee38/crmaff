import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AffiliateEventSource, AffiliateEventType


class AffiliateEventOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID | None
    partner: str
    source: AffiliateEventSource
    entered_by: uuid.UUID | None
    channel: str | None
    event_type: AffiliateEventType
    amount: float | None
    currency: str | None
    validation_flags: dict | None
    received_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}
