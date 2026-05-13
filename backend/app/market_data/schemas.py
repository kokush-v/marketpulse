from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str


class HistoryRange(StrEnum):
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    ONE_YEAR = "1Y"


class HistoryResolution(StrEnum):
    DAILY = "D"


class SymbolSearchResult(BaseModel):
    symbol: str
    display_symbol: str | None = None
    description: str | None = None
    type: str | None = None


class SymbolSearchResponse(BaseModel):
    query: str
    results: list[SymbolSearchResult]


class QuoteResponse(BaseModel):
    symbol: str
    current_price: float = Field(..., ge=0)
    daily_change: float | None = None
    daily_percent_change: float | None = None
    open_price: float | None = Field(default=None, ge=0)
    high_price: float | None = Field(default=None, ge=0)
    low_price: float | None = Field(default=None, ge=0)
    previous_close: float | None = Field(default=None, ge=0)
    quote_timestamp: datetime | None = None


class HistoryPoint(BaseModel):
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float


class HistoryResponse(BaseModel):
    symbol: str
    range: HistoryRange
    resolution: HistoryResolution
    points: list[HistoryPoint]


def unix_seconds_to_datetime(value: int | float | None) -> datetime | None:
    if value is None or value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=UTC)
