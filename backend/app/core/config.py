from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://arya:arya@localhost:5432/arya_jobs"
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "openai"  # openai | gemini

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o-mini"

    gemini_api_key: str = ""
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_llm_model: str = "gemini-2.5-flash-lite"

    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.2

    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"
    backend_cors_origin_regex: str = r"https://.*\.onrender\.com"
    shortlist_size: int = 12
    match_cache_ttl_seconds: int = 3600
    resume_embedding_cache_ttl_seconds: int = 86400
    job_embedding_cache_ttl_seconds: int = 604800

    log_level: str = "INFO"
    log_json: bool = False

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        pattern = self.backend_cors_origin_regex.strip()
        return pattern or None

    @property
    def uses_gemini(self) -> bool:
        return self.llm_provider.strip().lower() == "gemini"

    @property
    def embedding_model_name(self) -> str:
        if self.uses_gemini:
            return self.gemini_embedding_model
        return self.openai_embedding_model

    @property
    def llm_model_name(self) -> str:
        if self.uses_gemini:
            return self.gemini_llm_model
        return self.openai_llm_model

    @property
    def embedding_fingerprint(self) -> str:
        return f"{self.llm_provider.strip().lower()}:{self.embedding_model_name}"

    @property
    def api_key_env_name(self) -> str:
        return "GEMINI_API_KEY" if self.uses_gemini else "OPENAI_API_KEY"

    @property
    def database_url_async(self) -> str:
        """Normalize cloud Postgres URLs for asyncpg (Neon, Render, etc.)."""
        url = self.database_url.strip()
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    def has_llm_credentials(self) -> bool:
        if self.uses_gemini:
            key = self.gemini_api_key.strip()
            return bool(key and not key.startswith("your-"))
        key = self.openai_api_key.strip()
        return bool(key and not key.startswith("sk-your"))


settings = Settings()
