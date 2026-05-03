from pydantic import BaseModel, Field


class ProjectionInput(BaseModel):
    initial_amount: float = Field(..., ge=0)
    monthly_contribution: float = Field(..., ge=0)
    annual_return_pct: float
    years: int = Field(..., ge=1, le=50)
    euribor_pct: float = 0.0
