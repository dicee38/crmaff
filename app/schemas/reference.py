import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PartnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class PartnerOut(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChannelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ChannelOut(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ActiveToggle(BaseModel):
    is_active: bool
