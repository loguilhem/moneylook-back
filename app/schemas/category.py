from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=120)
    icon_html: str = Field(..., max_length=255)
    color: str = Field(..., max_length=20)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    icon_html: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=20)


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)