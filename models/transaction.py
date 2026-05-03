from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TransactionType(str, Enum):
    income = "Income"
    expense = "Expense"
    saving = "Saving"
    investment = "Investment"


class Transaction(BaseModel):
    entry_date: date
    month: str = Field(..., description="Month in YYYY-MM format")
    partner: str = Field(..., min_length=1, description="Custom partner name or Shared")
    transaction_type: TransactionType
    category: str
    subcategory: Optional[str] = None
    source: Optional[str] = None
    amount: float = Field(..., ge=0)
    notes: Optional[str] = None

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        if len(value) != 7 or value[4] != "-":
            raise ValueError("Month must use YYYY-MM format")
        return value

    @field_validator("partner")
    @classmethod
    def validate_partner(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Partner name cannot be empty")
        return value
