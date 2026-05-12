from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(BACKEND_ENV_FILE)


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=getenv("APP_NAME", "MarketPulse API"),
        app_version=getenv("APP_VERSION", "0.1.0"),
        database_url=getenv(
            "DATABASE_URL",
            "postgresql+psycopg://marketpulse:marketpulse@localhost:5432/marketpulse",
        ),
    )
