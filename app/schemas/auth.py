from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUserRead(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)
