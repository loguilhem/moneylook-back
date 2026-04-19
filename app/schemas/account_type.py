from pydantic import BaseModel, ConfigDict


class AccountTypeBase(BaseModel):
    name: str


class AccountTypeCreate(AccountTypeBase):
    pass


class AccountTypeUpdate(BaseModel):
    name: str | None = None


class AccountTypeRead(AccountTypeBase):
    id: int
    code: str | None = None
    is_system: bool = False

    model_config = ConfigDict(from_attributes=True)
