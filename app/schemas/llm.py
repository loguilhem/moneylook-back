from pydantic import BaseModel, ConfigDict, Field, field_validator


SUPPORTED_LLM_PROVIDERS = {"openai", "custom", "ollama"}


class LlmSettingsUpdate(BaseModel):
    enabled: bool = False
    provider: str = Field(default="openai", max_length=30)
    base_url: str = Field(default="", max_length=500)
    model: str = Field(default="", max_length=160)
    api_key: str | None = None
    organization: str = Field(default="", max_length=255)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        if normalized_value not in SUPPORTED_LLM_PROVIDERS:
            raise ValueError("Unsupported LLM provider")
        return normalized_value

    @field_validator("base_url", "model", "organization")
    @classmethod
    def strip_string(cls, value: str) -> str:
        return value.strip()

    @field_validator("api_key")
    @classmethod
    def strip_api_key(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class LlmSettingsRead(BaseModel):
    enabled: bool
    provider: str
    base_url: str
    model: str
    organization: str
    has_api_key: bool

    model_config = ConfigDict(from_attributes=True)


class LlmChatMessage(BaseModel):
    role: str = Field(..., max_length=20)
    content: str = Field(..., min_length=1, max_length=8000)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        if normalized_value not in {"assistant", "system", "user"}:
            raise ValueError("Unsupported message role")
        return normalized_value

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()


class LlmChatRequest(BaseModel):
    messages: list[LlmChatMessage] = Field(..., min_length=1, max_length=30)


class LlmChatResponse(BaseModel):
    message: LlmChatMessage


class LlmConnectionTestResponse(BaseModel):
    ok: bool
    message: str
