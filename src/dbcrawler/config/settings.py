from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    chat_model: str = "openrouter/free"
    embedding_model: str = "nvidia/nemotron-3-embed-1b"

    db_url: str = (
        "postgresql+psycopg://app_readonly:readonly_password@localhost:5433/dbcrawler"
    )
    db_admin_url: str = (
        "postgresql+psycopg://app_owner:owner_password@localhost:5433/dbcrawler"
    )

    similarity_threshold: float = 0.3
    sample_values_per_column: int = 5

    llm_timeout_seconds: float = 120.0
    llm_max_retries: int = 2

    guardrail_block_ddl: bool = True
    guardrail_block_dml: bool = True
    guardrail_max_subquery_depth: int = 3
    guardrail_max_limit_rows: int = 1000
    guardrail_max_scan_rows: int = 200000
    guardrail_enable_scan_cap: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
