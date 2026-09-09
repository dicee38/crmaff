import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import TaskStatus


class TaskCreate(BaseModel):
    lead_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    due_at: datetime | None = None
    manager_id: uuid.UUID | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    due_at: datetime | None = None
    status: TaskStatus | None = None
    manager_id: uuid.UUID | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    manager_id: uuid.UUID | None
    title: str
    due_at: datetime | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskOut]
    next_cursor: str | None = None
