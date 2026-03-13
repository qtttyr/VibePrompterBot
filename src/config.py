from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    gemini_api_key: str | None = None
    grok_api_key: str | None = None
    founder_password: str = "default_unsafe_password"
    admin_id: int | None = None


def load_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
