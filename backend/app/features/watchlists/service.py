from __future__ import annotations

from typing import Annotated

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.features.auth.models import User
from app.features.market_data.schemas import FeaturedAssetResponse
from app.features.market_data.service import MarketDataService
from app.features.watchlists.repository import WatchlistRepository
from app.features.watchlists.schemas import (
    AddWatchlistAssetRequest,
    WatchlistAssetContextResponse,
    WatchlistAssetResponse,
    WatchlistAssetSearchResponse,
    WatchlistAssetSearchResult,
    WatchlistAssetSummaryResponse,
    WatchlistNewsItemResponse,
    WatchlistOperationResponse,
    WatchlistResponse,
)


def get_watchlist_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> WatchlistRepository:
    return WatchlistRepository(session)


class WatchlistServiceError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class WatchlistService:
    def __init__(
        self,
        repository: Annotated[WatchlistRepository, Depends(get_watchlist_repository)],
        market_data_service: Annotated[MarketDataService, Depends()],
    ) -> None:
        self.repository = repository
        self.market_data_service = market_data_service

    async def get_watchlist(self, user: User) -> WatchlistResponse:
        assets = await self.repository.list_assets_for_user(user.id)
        return WatchlistResponse(
            assets=[WatchlistAssetResponse.model_validate(asset) for asset in assets]
        )

    async def search_assets(self, query: str) -> WatchlistAssetSearchResponse:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return WatchlistAssetSearchResponse(items=[])

        matches = await self.market_data_service.search_assets(normalized_query)
        items = [
            WatchlistAssetSearchResult(
                asset_id=asset.asset_id,
                symbol=asset.symbol,
                name=asset.name,
                market_cap_rank=asset.market_cap_rank,
                current_price=asset.current_price,
                price_change_percentage_24h=asset.price_change_percentage_24h,
                image_url=asset.image_url,
            )
            for asset in matches.items
        ]
        return WatchlistAssetSearchResponse(items=items)

    async def add_asset(
        self,
        user: User,
        payload: AddWatchlistAssetRequest,
    ) -> WatchlistAssetResponse:
        asset_id = payload.asset_id.strip().lower()
        symbol = payload.symbol.strip().upper()
        name = payload.name.strip()
        image_url = payload.image_url.strip() if payload.image_url else None

        existing = await self.repository.get_asset_for_user(user.id, asset_id)
        if existing is not None:
            raise WatchlistServiceError(
                status_code=status.HTTP_409_CONFLICT,
                message="Asset is already saved",
            )

        asset = await self.repository.create_asset_for_user(
            user_id=user.id,
            asset_id=asset_id,
            symbol=symbol,
            name=name,
            image_url=image_url,
        )
        return WatchlistAssetResponse.model_validate(asset)

    async def remove_asset(self, user: User, asset_id: str) -> WatchlistOperationResponse:
        deleted = await self.repository.delete_asset_for_user(user.id, asset_id.strip().lower())
        if not deleted:
            raise WatchlistServiceError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Saved asset not found",
            )
        return WatchlistOperationResponse(success=True)

    async def get_asset_context(self, user: User, asset_id: str) -> WatchlistAssetContextResponse:
        normalized_asset_id = asset_id.strip().lower()
        saved_asset = await self.repository.get_asset_for_user(user.id, normalized_asset_id)
        if saved_asset is None:
            raise WatchlistServiceError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Saved asset not found",
            )

        overview = await self.market_data_service.get_market_overview()
        asset = next(
            (
                featured
                for featured in overview.featured_assets
                if featured.id == normalized_asset_id
            ),
            None,
        )
        if asset is None:
            raise WatchlistServiceError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Selected asset context is unavailable right now",
            )

        return WatchlistAssetContextResponse(
            summary=self._build_summary(asset),
            chart=asset.chart,
            related_news=self._build_related_news(asset),
        )

    def _build_summary(self, asset: FeaturedAssetResponse) -> WatchlistAssetSummaryResponse:
        return WatchlistAssetSummaryResponse(
            asset_id=asset.id,
            symbol=asset.symbol,
            name=asset.name,
            market_cap_rank=asset.market_cap_rank,
            current_price=asset.current_price,
            price_change_24h=asset.price_change_24h,
            price_change_percentage_24h=asset.price_change_percentage_24h,
            market_cap=asset.market_cap,
            total_volume=asset.total_volume,
            high_24h=asset.high_24h,
            low_24h=asset.low_24h,
            image_url=asset.image_url,
            homepage=asset.homepage,
            description=asset.description,
            categories=asset.categories,
        )

    def _build_related_news(self, asset: FeaturedAssetResponse) -> list[WatchlistNewsItemResponse]:
        return [
            WatchlistNewsItemResponse(
                title=item.title,
                summary=item.summary,
                url=item.url,
                published_at=item.published_at,
                source=item.source,
            )
            for item in asset.related_news
        ]
