from decimal import Decimal

from pydantic import BaseModel


class FunnelResponse(BaseModel):
    clicks: int
    leads_created: int
    manager_assigned: int
    registered: int
    ftd: int
    commission_total: Decimal


class KpiResponse(BaseModel):
    total_leads: int
    total_registered: int
    total_ftd: int
    total_revenue: Decimal
    lead2reg_pct: float
    reg2fd_pct: float
