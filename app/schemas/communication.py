import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CommunicationChannel, CommunicationDirection


class CommunicationOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    manager_id: uuid.UUID | None
    channel: CommunicationChannel
    direction: CommunicationDirection
    message_text: str | None
    is_ai_suggested: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CommunicationListResponse(BaseModel):
    items: list[CommunicationOut]
    next_cursor: str | None = None


class CommunicationSendRequest(BaseModel):
    message_text: str = Field(min_length=1)
