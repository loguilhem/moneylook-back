from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ExpenseBase(BaseModel):
    date: date
    label: str = Field(..., max_length=255)
    amount_cents: int
    category_id: int
    bank_account_id: int


class ExpenseCreate(ExpenseBase):
    recurring_expense_id: int | None = None


class ExpenseUpdate(BaseModel):
    date: date
    label: str | None = Field(default=None, max_length=255)
    amount_cents: int | None = None
    category_id: int | None = None
    bank_account_id: int | None = None
    recurring_expense_id: int | None = None


class ExpenseRead(ExpenseBase):
    id: int
    recurring_expense_id: int | None = None

    model_config = ConfigDict(from_attributes=True)