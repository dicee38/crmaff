import uuid
from decimal import Decimal

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    manager_id: uuid.UUID
    label: str
    value: Decimal
    is_current_user: bool


class LeaderboardResponse(BaseModel):
    metric: str
    period: str
    total_participants: int
    rows: list[LeaderboardEntry]
    current_user_rank: int | None
    delta_to_rank_above: Decimal | None
    delta_over_rank_below: Decimal | None
