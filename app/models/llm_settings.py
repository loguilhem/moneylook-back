from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LlmSettings(Base):
    __tablename__ = "llm_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False, default="openai")
    base_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    api_key: Mapped[str] = mapped_column(Text, nullable=False, default="")
    organization: Mapped[str] = mapped_column(String(255), nullable=False, default="")
