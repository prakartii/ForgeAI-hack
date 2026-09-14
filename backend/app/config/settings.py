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

    # Database (Polyglot: SQLite System of Record + Neo4j Graph Projection)
    database_url: str = "sqlite:///./failurefoundry.db"
    neo4j_uri: Optional[str] = "bolt://localhost:7687"
    neo4j_user: Optional[str] = "neo4j"
    neo4j_password: Optional[str] = None
    neo4j_database: Optional[str] = "neo4j"

    # LLM Providers (Phase 3+)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # PRISM Integration (Phase 5+). Package blockconvey-monitor>=0.3.1
    # installs the `prismtrace` module (class prismtrace.PRISMtrace) --
    # verified by installing it and reading its source, not guessed.
    # Host confirmed against blockconvey.com/docs: prism.blockconvey.com,
    # not api.blockconvey.com (the earlier default here was wrong).
    prism_api_key: Optional[str] = None  # PRISM_API_KEY, format "pt-sk-..."
    prism_project_id: Optional[str] = None  # PRISM_PROJECT_ID, a uuid
    prism_base_url: str = "https://prism.blockconvey.com"
    # CLAUDE.md §23 requires PRISM evidence for a PASS. Kept True by default
    # (honest behavior: no credentials configured -> gate legitimately
    # BLOCKS); a team without PRISM access yet can set this False in .env
    # to explicitly acknowledge the gap rather than have it silently skipped.
    prism_evidence_required: bool = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
