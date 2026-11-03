from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.features.ai_assistant.schemas import (
    AssistantChartPayloadResponse,
    AssistantMessageSourceResponse,
    AssistantPendingActionSummaryResponse,
    AssistantPendingActionType,
)
from app.features.alerts.schemas import AlertScenario, AlertTimeBehavior, TriggerMode


class CoinQueryInput(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=120,
        description="Coin name, symbol, or asset ID",
    )


class PriceChartInput(BaseModel):
    coins: list[str] = Field(
        min_length=1,
        max_length=5,
        description="One to five unambiguous coin names or symbols.",
    )
    period: Literal["24h", "7d", "30d", "1y"] = Field(
        default="7d",
        description="Chart period. Use 7d when the user did not request a period.",
    )

    @field_validator("coins")
    @classmethod
    def validate_coins(cls, coins: list[str]) -> list[str]:
        normalized = [coin.strip() for coin in coins]
        if any(not coin for coin in normalized):
            raise ValueError("Coin names must not be blank")
        if len({coin.casefold() for coin in normalized}) != len(normalized):
            raise ValueError("Coins must be distinct")
        return normalized


class AssetProposalInput(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=120,
        description=(
            "The coin name or symbol the user wants to add to or remove from the watchlist. "
            "Ask which coin they mean if it is missing or ambiguous."
        ),
    )


class AlertProposalInput(BaseModel):
    asset: str | None = Field(
        default=None,
        max_length=120,
        description=(
            "The coin name or symbol for the alert. Ask the user which coin they mean when it "
            "has not been provided."
        ),
    )
    scenario: AlertScenario | None = Field(
        default=None,
        description=(
            "The internal alert condition: price_above means the market price reaches or rises "
            "above the target, price_below means it reaches or falls below the target, and "
            "coin_news means new articles about the coin. Keep these values internal and describe "
            "the condition naturally to the user."
        ),
    )
    time_behavior: AlertTimeBehavior = Field(
        default="one_time",
        description=(
            "The internal alert timing: one_time triggers once, while daily_recurring can trigger "
            "again on later days within its date range. Use one_time unless the user asks for the "
            "alert to repeat daily; do not ask the user about timing otherwise. Keep these values "
            "internal and describe the timing naturally to the user."
        ),
    )
    recurring_start_date: date | None = Field(
        default=None,
        description="First active date for a daily recurring alert.",
    )
    recurring_end_date: date | None = Field(
        default=None,
        description="Last active date for a daily recurring alert.",
    )
    trigger_mode: TriggerMode | None = Field(
        default=None,
        description=(
            "How to interpret the price threshold: currency is a fixed USD price and percent is "
            "a percentage price change. A threshold stated with $, USD, or dollars is currency; "
            "a threshold stated with % or percent is percent. Set it only from a unit the user "
            "stated; never infer it from the size of the number. When the threshold has no "
            "unit, ask the user which one they mean instead of calling this tool. Keep these "
            "values internal and use natural wording with the user. This is not applicable to "
            "news alerts."
        ),
    )
    threshold_value: float | None = Field(
        default=None,
        gt=0,
        description=(
            "The fixed USD price when the threshold uses currency, or the percentage change when "
            "it uses percent. This is not applicable to news alerts."
        ),
    )


class AlertTargetInput(BaseModel):
    alert: str = Field(
        min_length=1,
        max_length=200,
        description=(
            "The coin name or symbol of the user's alert, optionally followed by its condition "
            "when the user mentioned it, for example 'Bitcoin' or 'Solana price above $200'."
        ),
    )


class UpdateAlertProposalInput(AlertProposalInput):
    alert: str = Field(
        min_length=1,
        max_length=200,
        description=(
            "The coin name or symbol of the alert to update, optionally followed by its current "
            "condition when the user mentioned it, for example 'Bitcoin'."
        ),
    )


ToolStatus = Literal[
    "ok",
    "not_found",
    "partial_match",
    "clarification_needed",
    "confirmation_required",
    "error",
]


class ToolResult[ToolData: BaseModel](BaseModel):
    status: ToolStatus
    data: ToolData

    def __str__(self) -> str:
        """Keep LangChain tool messages JSON-serializable without losing type safety."""
        return self.model_dump_json()


@dataclass
class ChartPayloadCapture:
    payload: AssistantChartPayloadResponse | None = None


@dataclass
class SourcesCapture:
    """Sources of the data returned by tools during one response, deduplicated."""

    sources: list[AssistantMessageSourceResponse] = field(default_factory=list)

    def add(self, source: AssistantMessageSourceResponse) -> None:
        key = source_key(source)
        if all(source_key(existing) != key for existing in self.sources):
            self.sources.append(source)


def source_key(source: AssistantMessageSourceResponse) -> tuple[str, str | None]:
    return (source.kind, source.url if source.kind == "news" else source.title)


class CoinSummary(BaseModel):
    symbol: str
    name: str
    description: str | None = None
    current_price: float
    price_change_percentage_24h: float
    market_cap_rank: int | None = None


class CoinOverviewLookupData(BaseModel):
    coin: CoinSummary | None = None
    message: str | None = None
    matches: list[CoinSummary] = Field(default_factory=list)
    updated_at: str | None = None
    stale: bool = False


class NewsArticleData(BaseModel):
    title: str
    summary: str
    url: str
    published_at: str | None = None
    source: str


class CoinNewsData(BaseModel):
    articles: list[NewsArticleData]


class AssetData(BaseModel):
    symbol: str
    name: str


class WatchlistAssetsData(BaseModel):
    assets: list[AssetData]


class AlertData(BaseModel):
    coin: str
    status: str
    rule: str
    schedule: str


class AlertsData(BaseModel):
    alerts: list[AlertData]


class ChartSeriesSummaryData(BaseModel):
    symbol: str
    name: str
    point_count: int
    start_price: float
    end_price: float
    low_price: float
    high_price: float
    change_percentage: float
    updated_at: str | None = None
    stale: bool = False


class PriceChartData(BaseModel):
    period: Literal["24h", "7d", "30d", "1y"]
    series: list[ChartSeriesSummaryData]


class AssetClarificationData(BaseModel):
    message: str
    query: str | None = None
    matches: list[AssetData] = Field(default_factory=list)


class ChartAmbiguousAssetData(BaseModel):
    query: str
    matches: list[AssetData]


class ChartClarificationData(BaseModel):
    message: str
    not_found: list[str] = Field(default_factory=list)
    ambiguous: list[ChartAmbiguousAssetData] = Field(default_factory=list)


class AlertClarificationData(BaseModel):
    message: str
    matches: list[AlertData] = Field(default_factory=list)


class MissingAlertData(BaseModel):
    message: str
    missing_fields: list[str]


class PendingProposalData(BaseModel):
    action_type: AssistantPendingActionType
    summary: AssistantPendingActionSummaryResponse


class ToolErrorData(BaseModel):
    message: str
