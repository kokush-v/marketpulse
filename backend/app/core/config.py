from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MarketPulse API"
    database_url: str = (
        "postgresql+asyncpg://marketpulse:marketpulse@localhost:5432/marketpulse_dev"
    )
    test_database_url: str = (
        "postgresql+asyncpg://marketpulse:marketpulse@localhost:5433/marketpulse_test"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
