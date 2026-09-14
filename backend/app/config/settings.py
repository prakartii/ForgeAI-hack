from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    Follows CLAUDE.md §5 and §32.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application
    app_name: str = "FailureFoundry"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Network / Host
    host: str = "127.0.0.1"
    port: int = 8000
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = "sqlite:///./failurefoundry.db"

    # LLM Providers (Phase 3+)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # PRISM Monitor Integration (Phase 5+)
    prism_api_key: Optional[str] = None
    prism_project_id: Optional[str] = None
    prism_base_url: str = "https://api.blockconvey.com"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
