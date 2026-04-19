from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    CSRF_TRUSTED_ORIGINS: str = ""
    LOGIN_BRUTE_FORCE_ENABLED: bool = True
    SESSION_COOKIE_SECURE: bool = False

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
