from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.features.market_data.schemas import CryptoChartPointResponse


class WatchlistAssetResponse(BaseModel):
    id: UUID
    asset_id: str
    symbol: str
    name: str
    image_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AddWatchlistAssetRequest(BaseModel):
    asset_id: str = Field(min_length=1, max_length=120)
    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    image_url: str | None = Field(default=None, max_length=500)


class WatchlistAssetSearchResult(BaseModel):
    asset_id: str
    symbol: str
    name: str
    market_cap_rank: int
    current_price: float
    price_change_percentage_24h: float
    image_url: str


class WatchlistAssetSearchResponse(BaseModel):
    items: list[WatchlistAssetSearchResult]


class WatchlistAssetSummaryResponse(BaseModel):
    asset_id: str
    symbol: str
    name: str
    market_cap_rank: int
    current_price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap: float
    total_volume: float
    high_24h: float
    low_24h: float
    image_url: str
    homepage: str
    description: str
    categories: list[str]


class WatchlistNewsItemResponse(BaseModel):
    title: str
    summary: str
    url: str
    published_at: str
    source: str


class WatchlistAssetContextResponse(BaseModel):
    summary: WatchlistAssetSummaryResponse
    chart: list[CryptoChartPointResponse]
    related_news: list[WatchlistNewsItemResponse]


class WatchlistResponse(BaseModel):
    assets: list[WatchlistAssetResponse]


class WatchlistOperationResponse(BaseModel):
    success: bool


class WatchlistErrorResponse(BaseModel):
    message: str
