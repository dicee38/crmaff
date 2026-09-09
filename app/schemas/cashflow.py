from decimal import Decimal

from pydantic import BaseModel


class CashflowRow(BaseModel):
    key: str | None = None
    label: str | None = None
    reg: int
    fd_count: int
    fd_sum: Decimal
    rd_count: int
    rd_sum: Decimal
    cashflow: Decimal
    lead2reg_pct: float | None
    reg2fd_pct: float


class CashflowReportResponse(BaseModel):
    total: CashflowRow
    groups: list[CashflowRow]
