from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["local", "openai", "anthropic", "fake"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./home_energy_advisor.db"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    llm_provider: LLMProvider = "local"
    llm_model: str = "local-model"
    llm_api_base: str = "http://localhost:1234/v1"
    llm_api_key: str = "not-needed-for-local"

    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-4-5-haiku-latest"

    llm_timeout_seconds: int = 30
    llm_max_retries: int = 1
    llm_temperature: float = 0.2

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
