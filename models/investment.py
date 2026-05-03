from enum import Enum
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class InvestmentAllocation(BaseModel):
    etf_category: str
    allocation_pct: float = Field(..., ge=0, le=100)
    expected_return_pct: float = Field(..., ge=-20, le=30)
    risk_level: RiskLevel
