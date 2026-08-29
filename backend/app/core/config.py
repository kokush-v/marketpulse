from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MarketPulse API"
    database_url: str = (
        "postgresql+asyncpg://marketpulse:marketpulse@localhost:5432/marketpulse_dev"
    )
    test_database_url: str = (
        "postgresql+asyncpg://marketpulse:marketpulse@localhost:5433/marketpulse_test"
    )
    supabase_url: str = "https://example.supabase.co"
    supabase_anon_key: str = "replace-me"
    supabase_secret_key: str | None = None
    supabase_jwt_algorithm: str = "RS256"
    supabase_jwt_audience: str = "authenticated"
    frontend_url: str = "http://localhost:3000"
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    market_data_api_base_url: str = "http://localhost:3001"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 30.0
    groq_max_retries: int = 2
    groq_max_tokens: int = 1024
    assistant_max_tool_calls: int = 4
    assistant_max_context_messages: int = 10
    assistant_max_context_characters: int = 12_000
    telegram_bot_token: str = "replace-me"
    telegram_bot_username: str = "marketpulse_bot"
    telegram_link_token_ttl_seconds: int = 900
    telegram_test_notification_cooldown_seconds: int = 10
    telegram_webhook_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def supabase_jwt_issuer(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_jwt_issuer}/.well-known/jwks.json"

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


settings = Settings()
