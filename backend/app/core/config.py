from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://arya:arya@localhost:5432/arya_jobs"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o-mini"

    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.2

    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"
    shortlist_size: int = 12
    match_cache_ttl_seconds: int = 3600
    resume_embedding_cache_ttl_seconds: int = 86400
    job_embedding_cache_ttl_seconds: int = 604800

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()
