from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Frequency = Literal["weekly", "monthly", "yearly"]
DatePolicy = Literal["same_day", "last_day_of_month", "first_business_day", "last_business_day"]


class RecurringExpenseBase(BaseModel):
    label: str = Field(..., max_length=255)
    amount_cents: int
    is_active: bool = True
    date_policy: DatePolicy = "same_day"
    frequency: Frequency = "monthly"
    category_id: int
    bank_account_id: int


class RecurringExpenseCreate(RecurringExpenseBase):
    pass


class RecurringExpenseUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=255)
    amount_cents: int | None = None
    is_active: bool | None = None
    date_policy: DatePolicy | None = None
    frequency: Frequency | None = None
    category_id: int | None = None
    bank_account_id: int | None = None


class RecurringExpenseRead(RecurringExpenseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
