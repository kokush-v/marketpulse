from pydantic import BaseModel


class CryptoChartPointResponse(BaseModel):
    time: str
    price: float
    volume: float


class FeaturedAssetResponse(BaseModel):
    id: str
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
    chart: list[CryptoChartPointResponse]


class CryptoMoverResponse(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap_rank: int
    image_url: str


class MarketOverviewResponse(BaseModel):
    generated_at: str
    source: str
    ranking_basis: str
    hero_asset_id: str | None
    featured_assets: list[FeaturedAssetResponse]
    hero_chart: list[CryptoChartPointResponse] | None
    top_gainers: list[CryptoMoverResponse]
    top_losers: list[CryptoMoverResponse]


class MarketOverviewErrorResponse(BaseModel):
    message: str
