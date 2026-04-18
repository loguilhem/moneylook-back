from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class IncomeBase(BaseModel):
    date: date
    label: str = Field(..., max_length=255)
    amount_cents: int
    category_id: int | None = None
    bank_account_id: int


class IncomeCreate(IncomeBase):
    recurring_income_id: int | None = None


class IncomeUpdate(BaseModel):
    date: date
    label: str | None = Field(default=None, max_length=255)
    amount_cents: int | None = None
    category_id: int | None = None
    bank_account_id: int | None = None
    recurring_income_id: int | None = None


class IncomeRead(IncomeBase):
    id: int
    recurring_income_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
