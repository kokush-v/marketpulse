from pydantic import BaseModel, Field


class CryptoChartPointResponse(BaseModel):
    time: str
    price: float
    volume: float


class RelatedNewsItemResponse(BaseModel):
    title: str
    summary: str
    url: str
    published_at: str
    source: str


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
    related_news: list[RelatedNewsItemResponse] = Field(default_factory=list)


class CryptoMoverResponse(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap_rank: int
    image_url: str


class AssetSearchResultResponse(BaseModel):
    asset_id: str
    symbol: str
    name: str
    market_cap_rank: int
    current_price: float
    price_change_percentage_24h: float
    image_url: str


class AssetSearchResponse(BaseModel):
    items: list[AssetSearchResultResponse]


class CoinNewsArticleResponse(BaseModel):
    title: str
    summary: str
    url: str
    image_url: str | None = None
    published_at: str | None = None
    source: str


class CoinNewsSearchResponse(BaseModel):
    articles: list[CoinNewsArticleResponse]


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
