import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AffiliateEventType


class AffiliateEventOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID | None
    partner: str
    event_type: AffiliateEventType
    amount: float | None
    currency: str | None
    received_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}
