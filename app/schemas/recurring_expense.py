from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Frequency = Literal["hebdomadaire", "mensuel", "annuel"]


class RecurringExpenseBase(BaseModel):
    label: str = Field(..., max_length=255)
    amount_cents: int
    start_date: date
    end_date: date | None = None
    frequency: Frequency = "mensuel"
    category_id: int
    bank_account_id: int


class RecurringExpenseCreate(RecurringExpenseBase):
    pass


class RecurringExpenseUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=255)
    amount_cents: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    frequency: Frequency | None = None
    category_id: int | None = None
    bank_account_id: int | None = None


class RecurringExpenseRead(RecurringExpenseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
