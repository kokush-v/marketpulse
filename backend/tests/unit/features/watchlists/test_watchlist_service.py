from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.features.auth.models import User
from app.features.market_data.schemas import (
    AssetSearchResponse,
    AssetSearchResultResponse,
    CryptoChartPointResponse,
    FeaturedAssetResponse,
    MarketOverviewResponse,
    RelatedNewsItemResponse,
)
from app.features.watchlists.models import WatchlistAsset
from app.features.watchlists.schemas import AddWatchlistAssetRequest
from app.features.watchlists.service import WatchlistService, WatchlistServiceError


class FakeWatchlistRepository:
    def __init__(self, assets: list[WatchlistAsset] | None = None) -> None:
        self.assets = assets or []

    async def list_assets_for_user(self, user_id):
        return [asset for asset in self.assets if asset.user_id == user_id]

    async def get_asset_for_user(self, user_id, asset_id):
        for asset in self.assets:
            if asset.user_id == user_id and asset.asset_id == asset_id:
                return asset
        return None

    async def create_asset_for_user(self, user_id, asset_id, symbol, name, image_url):
        asset = WatchlistAsset(
            id=uuid4(),
            user_id=user_id,
            asset_id=asset_id,
            symbol=symbol,
            name=name,
            image_url=image_url,
            created_at=datetime.now(tz=UTC),
        )
        self.assets.append(asset)
        return asset

    async def delete_asset_for_user(self, user_id, asset_id):
        before = len(self.assets)
        self.assets = [
            asset
            for asset in self.assets
            if not (asset.user_id == user_id and asset.asset_id == asset_id)
        ]
        return len(self.assets) != before


class FakeMarketDataService:
    def __init__(self, featured_assets: list[FeaturedAssetResponse]) -> None:
        self.featured_assets = featured_assets

    async def get_market_overview(self):
        return MarketOverviewResponse(
            generated_at="2026-05-22T10:00:00Z",
            source="market-data-api",
            ranking_basis="Top assets",
            hero_asset_id=self.featured_assets[0].id if self.featured_assets else None,
            featured_assets=self.featured_assets,
            hero_chart=self.featured_assets[0].chart if self.featured_assets else None,
            top_gainers=[],
            top_losers=[],
        )

    async def search_assets(self, query: str) -> AssetSearchResponse:
        normalized_query = query.strip().lower()
        matches = [
            AssetSearchResultResponse(
                asset_id=asset.id,
                symbol=asset.symbol,
                name=asset.name,
                market_cap_rank=asset.market_cap_rank,
                current_price=asset.current_price,
                price_change_percentage_24h=asset.price_change_percentage_24h,
                image_url=asset.image_url,
            )
            for asset in self.featured_assets
            if normalized_query in asset.id.lower()
            or normalized_query in asset.symbol.lower()
            or normalized_query in asset.name.lower()
        ]
        return AssetSearchResponse(items=matches)


def _make_user() -> User:
    return User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="watcher@example.com",
        created_at=datetime.now(tz=UTC),
    )


def _make_featured_asset(asset_id: str = "bitcoin", symbol: str = "BTC", name: str = "Bitcoin"):
    return FeaturedAssetResponse(
        id=asset_id,
        symbol=symbol,
        name=name,
        market_cap_rank=1,
        current_price=100000.0,
        price_change_24h=1200.0,
        price_change_percentage_24h=1.2,
        market_cap=2_000_000_000_000.0,
        total_volume=50_000_000_000.0,
        high_24h=101000.0,
        low_24h=98000.0,
        image_url="https://example.com/asset.png",
        homepage="https://example.com",
        description="Asset description",
        categories=["Store of Value"],
        chart=[
            CryptoChartPointResponse(time="2026-05-21T10:00:00Z", price=99000.0, volume=0.0),
            CryptoChartPointResponse(time="2026-05-22T10:00:00Z", price=100000.0, volume=0.0),
        ],
        related_news=[
            RelatedNewsItemResponse(
                title=f"{name} climbs on institutional demand",
                summary=f"{name} remains in focus after a strong session.",
                url=f"https://example.com/{asset_id}/news",
                published_at="2026-05-22T09:00:00Z",
                source="CoinGecko",
            )
        ],
    )


@pytest.mark.asyncio
async def test_add_asset_prevents_duplicates() -> None:
    user = _make_user()
    existing_asset = WatchlistAsset(
        id=uuid4(),
        user_id=user.id,
        asset_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        image_url="https://example.com/asset.png",
        created_at=datetime.now(tz=UTC),
    )
    service = WatchlistService(
        repository=FakeWatchlistRepository([existing_asset]),
        market_data_service=FakeMarketDataService([_make_featured_asset()]),
    )

    with pytest.raises(WatchlistServiceError) as exc_info:
        await service.add_asset(
            user,
            AddWatchlistAssetRequest(
                asset_id="bitcoin",
                symbol="btc",
                name="Bitcoin",
                image_url="https://example.com/asset.png",
            ),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.message == "Asset is already saved"


@pytest.mark.asyncio
async def test_add_and_remove_asset_round_trip() -> None:
    user = _make_user()
    repository = FakeWatchlistRepository()
    service = WatchlistService(
        repository=repository,
        market_data_service=FakeMarketDataService([_make_featured_asset()]),
    )

    created = await service.add_asset(
        user,
        AddWatchlistAssetRequest(
            asset_id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            image_url="https://example.com/asset.png",
        ),
    )
    removed = await service.remove_asset(user, "bitcoin")

    assert created.asset_id == "bitcoin"
    assert created.symbol == "BTC"
    assert created.image_url == "https://example.com/asset.png"
    assert removed.success is True
    assert repository.assets == []


@pytest.mark.asyncio
async def test_get_asset_context_returns_selected_asset_data() -> None:
    user = _make_user()
    saved_asset = WatchlistAsset(
        id=uuid4(),
        user_id=user.id,
        asset_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        image_url="https://example.com/asset.png",
        created_at=datetime.now(tz=UTC),
    )
    service = WatchlistService(
        repository=FakeWatchlistRepository([saved_asset]),
        market_data_service=FakeMarketDataService([_make_featured_asset()]),
    )

    context = await service.get_asset_context(user, "bitcoin")

    assert context.summary.asset_id == "bitcoin"
    assert len(context.chart) == 2
    assert context.related_news[0].url == "https://example.com/bitcoin/news"
    assert context.related_news[0].source == "CoinGecko"


@pytest.mark.asyncio
async def test_get_watchlist_returns_only_user_owned_assets() -> None:
    user = _make_user()
    other_user = _make_user()
    owned_asset = WatchlistAsset(
        id=uuid4(),
        user_id=user.id,
        asset_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        image_url="https://example.com/asset.png",
        created_at=datetime.now(tz=UTC),
    )
    foreign_asset = WatchlistAsset(
        id=uuid4(),
        user_id=other_user.id,
        asset_id="ethereum",
        symbol="ETH",
        name="Ethereum",
        image_url="https://example.com/eth.png",
        created_at=datetime.now(tz=UTC),
    )
    service = WatchlistService(
        repository=FakeWatchlistRepository([owned_asset, foreign_asset]),
        market_data_service=FakeMarketDataService([_make_featured_asset()]),
    )

    result = await service.get_watchlist(user)

    assert [asset.asset_id for asset in result.assets] == ["bitcoin"]
    assert result.assets[0].image_url == "https://example.com/asset.png"


@pytest.mark.asyncio
async def test_search_assets_returns_market_data_matches() -> None:
    service = WatchlistService(
        repository=FakeWatchlistRepository(),
        market_data_service=FakeMarketDataService(
            [
                _make_featured_asset(asset_id="bitcoin", symbol="BTC", name="Bitcoin"),
                _make_featured_asset(asset_id="ethereum", symbol="ETH", name="Ethereum"),
            ]
        ),
    )

    result = await service.search_assets("eth")

    assert [asset.asset_id for asset in result.items] == ["ethereum"]
    assert result.items[0].symbol == "ETH"
