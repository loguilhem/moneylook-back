from pydantic import BaseModel, ConfigDict, Field


class BankAccountBase(BaseModel):
    label: str = Field(..., max_length=120)
    currency: str = Field(default="CHF", min_length=3, max_length=3)
    initial_balance_cents: int = 0
    is_default: bool = False
    account_type_id: int


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=120)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    initial_balance_cents: int | None = None
    is_default: bool | None = None
    account_type_id: int | None = None


class BankAccountRead(BankAccountBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
