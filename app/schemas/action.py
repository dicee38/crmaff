import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import AffiliateEventSource, AffiliateEventType

# Типы действий, доступные для ручного ввода (см. CLAUDE.md, "Ручной ввод действий МОП").
MANUAL_ACTION_TYPES = {"registration", "ftd", "deposit", "withdrawal", "chargeback"}
AMOUNT_REQUIRED_TYPES = {"ftd", "deposit", "withdrawal"}


class ManualActionCreate(BaseModel):
    player_id: str = Field(min_length=1, description="external_click_id или telegram_user_id игрока")
    partner_name: str
    channel: str | None = None
    event_type: str
    amount: Decimal | None = None
    currency: str = "USD"
    occurred_at: datetime | None = None

    @field_validator("event_type")
    @classmethod
    def _validate_event_type(cls, value: str) -> str:
        if value not in MANUAL_ACTION_TYPES:
            raise ValueError(f"event_type must be one of {sorted(MANUAL_ACTION_TYPES)}")
        return value


class ActionAggregates(BaseModel):
    total_actions: int
    lead_count: int
    deposit_count: int
    deposit_sum: Decimal


class ActionRow(BaseModel):
    """Строка журнала действий (/actions) - обогащена данными по лиду/менеджеру
    для отображения в UI-таблице (см. CLAUDE.md, раздел "Список действий")."""

    id: uuid.UUID
    received_at: datetime
    partner: str
    channel: str | None
    event_type: AffiliateEventType
    source: AffiliateEventSource
    player_external_id: str | None
    amount: Decimal | None
    currency: str | None
    lead_id: uuid.UUID | None
    manager_full_name: str | None
    manager_role: str | None
    validation_flags: dict | None


class ActionListResponse(BaseModel):
    items: list[ActionRow]
    next_cursor: str | None = None
    aggregates: ActionAggregates
