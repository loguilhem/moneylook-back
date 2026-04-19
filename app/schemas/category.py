import re

from pydantic import BaseModel, ConfigDict, Field
from pydantic import field_validator


ICON_TAG_PATTERN = re.compile(r'^<i\s+class=["\']([^"\']+)["\']\s*></i>$')
ICON_CLASS_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')


def sanitize_icon_html(value: str) -> str:
    raw_value = value.strip()
    match = ICON_TAG_PATTERN.fullmatch(raw_value)
    class_value = match.group(1) if match else raw_value
    classes = class_value.split()

    if not classes or not all(ICON_CLASS_PATTERN.fullmatch(class_name) for class_name in classes):
        raise ValueError("icon_html must contain FontAwesome classes only")

    if not any(class_name.startswith("fa-") or class_name in {"fa", "fas", "far", "fab"} for class_name in classes):
        raise ValueError("icon_html must contain a FontAwesome class")

    return f'<i class="{" ".join(classes)}"></i>'


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=120)
    icon_html: str = Field(..., max_length=255)
    color: str = Field(..., max_length=20)

    @field_validator("icon_html")
    @classmethod
    def validate_icon_html(cls, value: str) -> str:
        return sanitize_icon_html(value)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    icon_html: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=20)

    @field_validator("icon_html")
    @classmethod
    def validate_icon_html(cls, value: str | None) -> str | None:
        return sanitize_icon_html(value) if value is not None else None


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
