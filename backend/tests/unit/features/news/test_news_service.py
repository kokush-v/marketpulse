from __future__ import annotations

import pytest

from app.features.news.service import NewsService, NewsServiceError


class StubMarketDataService:
    def __init__(self, articles: list[dict[str, object]] | None = None) -> None:
        self.articles = articles or []
        self.calls: list[str] = []

    async def get_coin_news(self, query: str):
        self.calls.append(query)
        return type(
            "StubResponse",
            (),
            {"articles": [type("Article", (), article)() for article in self.articles]},
        )()


@pytest.mark.asyncio
async def test_news_service_normalizes_upstream_articles() -> None:
    market_data_service = StubMarketDataService(
        articles=[
            {
                "title": "Bitcoin ETF flows stay positive",
                "summary": "Demand remained firm through the US session.",
                "url": "https://example.com/news/bitcoin-etf",
                "image_url": "https://example.com/news/bitcoin-etf.png",
                "published_at": "2026-05-25T10:00:00Z",
                "source": "NewsAPI",
            }
        ]
    )

    service = NewsService(market_data_service=market_data_service)
    result = await service.search_coin_news(" bitcoin ")

    assert market_data_service.calls == ["bitcoin"]
    assert result.query == "bitcoin"
    assert result.articles[0].title == "Bitcoin ETF flows stay positive"
    assert result.articles[0].image_url == "https://example.com/news/bitcoin-etf.png"


@pytest.mark.asyncio
async def test_news_service_rejects_blank_query_without_upstream_lookup() -> None:
    market_data_service = StubMarketDataService()
    service = NewsService(market_data_service=market_data_service)

    with pytest.raises(NewsServiceError) as exc_info:
        await service.search_coin_news("   ")

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Query must not be blank"
    assert market_data_service.calls == []
