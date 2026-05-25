from __future__ import annotations

from typing import Annotated

from fastapi import Depends, status

from app.features.market_data.service import MarketDataService
from app.features.news.schemas import NewsArticleResponse, NewsSearchResponse


class NewsServiceError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class NewsService:
    def __init__(
        self,
        market_data_service: Annotated[MarketDataService, Depends()],
    ) -> None:
        self.market_data_service = market_data_service

    async def search_coin_news(self, query: str) -> NewsSearchResponse:
        normalized_query = query.strip()
        if not normalized_query:
            raise NewsServiceError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                message="Query must not be blank",
            )

        upstream_response = await self.market_data_service.get_coin_news(normalized_query)
        return NewsSearchResponse(
            query=normalized_query,
            articles=[
                NewsArticleResponse(
                    title=article.title,
                    summary=article.summary,
                    url=article.url,
                    image_url=article.image_url,
                    published_at=article.published_at,
                    source=article.source,
                )
                for article in upstream_response.articles
            ],
        )
