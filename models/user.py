from pydantic import BaseModel


class PartnerProfile(BaseModel):
    name: str
    monthly_income: float = 0.0
