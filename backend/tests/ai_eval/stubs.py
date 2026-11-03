"""In-memory services behind assistant tools for evals.

They return fixed, valid data so a scenario outcome depends only on the agent's tool choices,
and they record every proposal and attempted mutation for confirmation-boundary checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

from app.features.ai_assistant.schemas import (
    AssistantPendingActionResponse,
    AssistantPendingActionSummaryResponse,
)

COINS: list[dict[str, Any]] = [
    {
        "asset_id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin",
        "current_price": 100_000.0,
        "price_change_percentage_24h": 2.04,
        "market_cap_rank": 1,
    },
    {
        "asset_id": "ethereum",
        "symbol": "ETH",
        "name": "Ethereum",
        "current_price": 3_500.0,
        "price_change_percentage_24h": -1.2,
        "market_cap_rank": 2,
    },
    {
        "asset_id": "solana",
        "symbol": "SOL",
        "name": "Solana",
        "current_price": 180.0,
        "price_change_percentage_24h": 4.5,
        "market_cap_rank": 5,
    },
    {
        "asset_id": "dogecoin",
        "symbol": "DOGE",
        "name": "Dogecoin",
        "current_price": 0.21,
        "price_change_percentage_24h": 0.8,
        "market_cap_rank": 8,
    },
]
WATCHLIST_ASSET_IDS = ("bitcoin", "ethereum", "solana")
ALERTS: list[dict[str, Any]] = [
    {
        "asset_id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin",
        "status": "active",
        "rule_summary": "Price above $120,000",
        "time_summary": "One-time",
    },
    {
        "asset_id": "ethereum",
        "symbol": "ETH",
        "name": "Ethereum",
        "status": "paused",
        "rule_summary": "Price below $3,000",
        "time_summary": "One-time",
    },
    {
        "asset_id": "solana",
        "symbol": "SOL",
        "name": "Solana",
        "status": "active",
        "rule_summary": "Price above $200",
        "time_summary": "One-time",
    },
    {
        "asset_id": "solana",
        "symbol": "SOL",
        "name": "Solana",
        "status": "active",
        "rule_summary": "Any new coin news",
        "time_summary": "One-time",
    },
]


def _coin_matches(coin: dict[str, Any], query: str) -> bool:
    normalized = query.strip().casefold()
    return normalized in {
        coin["asset_id"].casefold(),
        coin["symbol"].casefold(),
        coin["name"].casefold(),
    }


def _asset(coin: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(**coin, image_url=f"https://example.com/{coin['asset_id']}.png")


@dataclass
class EvalRecorder:
    proposals: list[str] = field(default_factory=list)
    mutations: list[str] = field(default_factory=list)

    def reset(self) -> None:
        self.proposals.clear()
        self.mutations.clear()


class StubMarketDataService:
    async def get_market_overview(self) -> SimpleNamespace:
        return SimpleNamespace(
            featured_assets=[
                SimpleNamespace(
                    id=coin["asset_id"],
                    symbol=coin["symbol"],
                    name=coin["name"],
                    description=f"{coin['name']} is a cryptocurrency.",
                    current_price=coin["current_price"],
                    price_change_percentage_24h=coin["price_change_percentage_24h"],
                    market_cap_rank=coin["market_cap_rank"],
                )
                for coin in COINS
            ]
        )

    async def search_assets(self, query: str) -> SimpleNamespace:
        return SimpleNamespace(items=[_asset(coin) for coin in COINS if _coin_matches(coin, query)])

    async def get_historical_prices(self, *, asset_ids: list[str], period: str) -> SimpleNamespace:
        prices = {coin["asset_id"]: coin["current_price"] for coin in COINS}
        return SimpleNamespace(
            period=period,
            series=[
                SimpleNamespace(
                    asset_id=asset_id,
                    points=[
                        SimpleNamespace(time="2026-10-01T00:00:00Z", price=prices[asset_id] * 0.95),
                        SimpleNamespace(time="2026-10-02T00:00:00Z", price=prices[asset_id]),
                    ],
                )
                for asset_id in asset_ids
            ],
        )


class StubNewsService:
    async def search_coin_news(self, query: str) -> SimpleNamespace:
        return SimpleNamespace(
            query=query,
            articles=[
                SimpleNamespace(
                    title=f"{query} market update",
                    summary=f"Latest developments around {query}.",
                    url="https://example.com/news/1",
                    published_at="2026-10-02T08:00:00Z",
                    source="Example News",
                )
            ],
        )


class StubWatchlistService:
    def __init__(self, recorder: EvalRecorder) -> None:
        self.recorder = recorder

    async def get_watchlist(self, _user: object) -> SimpleNamespace:
        return SimpleNamespace(
            assets=[_asset(coin) for coin in COINS if coin["asset_id"] in WATCHLIST_ASSET_IDS]
        )

    async def search_assets(self, query: str) -> SimpleNamespace:
        return SimpleNamespace(items=[_asset(coin) for coin in COINS if _coin_matches(coin, query)])

    async def add_asset(self, *_args: object, **_kwargs: object) -> None:
        self.recorder.mutations.append("add_watchlist_asset")

    async def remove_asset(self, *_args: object, **_kwargs: object) -> None:
        self.recorder.mutations.append("remove_watchlist_asset")


class StubAlertService:
    def __init__(self, recorder: EvalRecorder) -> None:
        self.recorder = recorder

    async def list_alerts(self, _user: object) -> SimpleNamespace:
        return SimpleNamespace(items=[SimpleNamespace(id=uuid4(), **alert) for alert in ALERTS])

    async def create_alert(self, *_args: object, **_kwargs: object) -> None:
        self.recorder.mutations.append("create_alert")

    async def update_alert(self, *_args: object, **_kwargs: object) -> None:
        self.recorder.mutations.append("update_alert")

    async def pause_alert(self, *_args: object, **_kwargs: object) -> None:
        self.recorder.mutations.append("pause_alert")

    async def resume_alert(self, *_args: object, **_kwargs: object) -> None:
        self.recorder.mutations.append("resume_alert")

    async def delete_alert(self, *_args: object, **_kwargs: object) -> None:
        self.recorder.mutations.append("delete_alert")


class StubActionService:
    """Records proposals instead of persisting pending actions."""

    def __init__(self, recorder: EvalRecorder) -> None:
        self.recorder = recorder

    async def propose(
        self,
        *,
        action_type: str,
        summary: AssistantPendingActionSummaryResponse,
        **_kwargs: object,
    ) -> AssistantPendingActionResponse:
        self.recorder.proposals.append(action_type)
        return AssistantPendingActionResponse(
            id=uuid4(),
            action_type=action_type,  # type: ignore[arg-type]
            status="pending",
            summary=summary,
        )


def stub_user() -> Any:
    return SimpleNamespace(id=UUID(int=1))


def stub_conversation() -> Any:
    return SimpleNamespace(id=UUID(int=2))
