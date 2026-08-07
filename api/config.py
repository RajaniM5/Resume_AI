from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Resume AI Screening API"
    environment: str = "development"
    api_version: str = "v1"

    database_url: str = "postgresql+psycopg://localhost/resume_ai"
    redis_url: str = "redis://localhost:6379/0"

    # Comma-separated list of valid API keys. In production these are issued
    # per HR-system integration so calls can be attributed/revoked individually.
    api_keys: str = "dev-key"

    # Fixed-window request limit per API key. In-memory, per-process — fine for
    # single-instance MVP; move to a Redis-backed limiter before scaling out
    # to multiple API instances.
    rate_limit_per_minute: int = 60

    # Celery runs tasks synchronously in-process when true, so the API and its
    # tests work without a live broker/worker. Set false in real deployments.
    celery_task_always_eager: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_key_set(self) -> set[str]:
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}


settings = Settings()
