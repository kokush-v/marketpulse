from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.features.alerts.models import AlertRule
from app.features.background_jobs.service import (
    NEWS_ALERT_EVALUATION_CURSOR,
    PRICE_ALERT_EVALUATION_CURSOR,
    NewsAlertEvaluator,
    NewsScheduledAlertEvaluationService,
    PriceAlertEvaluator,
    PriceScheduledAlertEvaluationService,
)
from app.features.market_data.schemas import AssetSearchResultResponse, CoinNewsSearchResponse


class FakeAlertRepository:
    def __init__(self, alerts: list[AlertRule]) -> None:
        self.alerts = alerts
        self.selection_calls: list[tuple[str, date]] = []

    async def list_eligible_price_alerts_for_window(self, window_date: date) -> list[AlertRule]:
        self.selection_calls.append(("price", window_date))
        return self._filter_eligible_alerts(window_date, scenarios={"price_above", "price_below"})

    async def list_eligible_news_alerts_for_window(self, window_date: date) -> list[AlertRule]:
        self.selection_calls.append(("news", window_date))
        return self._filter_eligible_alerts(window_date, scenarios={"coin_news"})

    async def update_alert_runtime_state(
        self,
        alert: AlertRule,
        *,
        scenario_payload: dict[str, object],
    ) -> AlertRule:
        alert.scenario_payload = scenario_payload
        return alert

    async def record_trigger_result(
        self,
        alert: AlertRule,
        *,
        triggered_at: datetime,
        scenario_payload: dict[str, object],
        pause_after_trigger: bool,
    ) -> AlertRule:
        alert.last_triggered_on = triggered_at.date()
        alert.last_triggered_at = triggered_at
        alert.scenario_payload = scenario_payload
        if pause_after_trigger:
            alert.status = "paused"
        return alert

    def _filter_eligible_alerts(self, window_date: date, *, scenarios: set[str]) -> list[AlertRule]:
        eligible: list[AlertRule] = []
        for alert in self.alerts:
            if alert.status != "active":
                continue
            if str(alert.scenario_payload["scenario"]) not in scenarios:
                continue
            if alert.time_behavior == "one_time":
                eligible.append(alert)
                continue
            if (
                alert.recurring_start_date is None
                or alert.recurring_end_date is None
                or alert.recurring_start_date > window_date
                or alert.recurring_end_date < window_date
            ):
                continue
            eligible.append(alert)
        return eligible


class FakeJobRepository:
    def __init__(self, last_processed_window_end: datetime | None = None) -> None:
        self.cursors: dict[str, SimpleNamespace] = {}
        self.requested_names: list[str] = []
        self.advanced_names: list[str] = []
        if last_processed_window_end is not None:
            self.cursors[PRICE_ALERT_EVALUATION_CURSOR] = SimpleNamespace(
                name=PRICE_ALERT_EVALUATION_CURSOR,
                last_processed_window_end=last_processed_window_end,
            )
            self.cursors[NEWS_ALERT_EVALUATION_CURSOR] = SimpleNamespace(
                name=NEWS_ALERT_EVALUATION_CURSOR,
                last_processed_window_end=last_processed_window_end,
            )

    async def get_cursor(self, name: str):
        self.requested_names.append(name)
        return self.cursors.get(name)

    async def ensure_cursor(self, *, name: str, default_last_processed_window_end: datetime | None):
        cursor = SimpleNamespace(
            name=name,
            last_processed_window_end=default_last_processed_window_end,
        )
        self.cursors[name] = cursor
        return cursor

    async def advance_cursor(self, *, name: str, last_processed_window_end: datetime):
        self.advanced_names.append(name)
        cursor = SimpleNamespace(
            name=name,
            last_processed_window_end=last_processed_window_end,
        )
        self.cursors[name] = cursor
        return cursor


class FakeMarketDataService:
    def __init__(
        self,
        *,
        assets: dict[str, AssetSearchResultResponse] | None = None,
        news_by_name: dict[str, CoinNewsSearchResponse] | None = None,
        asset_sequence: list[AssetSearchResultResponse] | None = None,
        news_sequence: list[CoinNewsSearchResponse] | None = None,
    ) -> None:
        self.assets = assets or {}
        self.news_by_name = news_by_name or {}
        self.asset_sequence = asset_sequence or []
        self.news_sequence = news_sequence or []

    async def find_asset(self, *, asset_id: str, symbol: str, name: str):
        _ = symbol, name
        if self.asset_sequence:
            return self.asset_sequence.pop(0)
        return self.assets.get(asset_id)

    async def get_coin_news(self, query: str) -> CoinNewsSearchResponse:
        if self.news_sequence:
            return self.news_sequence.pop(0)
        return self.news_by_name.get(query, CoinNewsSearchResponse(articles=[]))


class FakeTelegramDispatcher:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def dispatch_scheduled_alert_notification(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(**kwargs)


def _make_price_asset(asset_id: str = "bitcoin", current_price: float = 105000.0):
    return AssetSearchResultResponse(
        asset_id=asset_id,
        symbol="BTC",
        name="Bitcoin",
        market_cap_rank=1,
        current_price=current_price,
        price_change_percentage_24h=2.5,
        image_url="https://example.com/asset.png",
    )


def _make_alert(
    *,
    scenario_payload: dict[str, object],
    time_behavior: str = "one_time",
    last_triggered_on: date | None = None,
    last_triggered_at: datetime | None = None,
    recurring_start_date: date | None = None,
    recurring_end_date: date | None = None,
) -> AlertRule:
    return AlertRule(
        id=uuid4(),
        user_id=uuid4(),
        asset_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        image_url="https://example.com/asset.png",
        status="active",
        time_behavior=time_behavior,
        recurring_start_date=recurring_start_date,
        recurring_end_date=recurring_end_date,
        arm_version=1,
        last_triggered_on=last_triggered_on,
        last_triggered_at=last_triggered_at,
        scenario_payload=scenario_payload,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


@pytest.mark.asyncio
async def test_price_service_uses_price_cursor_and_factory_method() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "price_above",
            "trigger_mode": "currency",
            "threshold_value": 100000.0,
        }
    )
    alert_repository = FakeAlertRepository([alert])
    job_repository = FakeJobRepository(
        last_processed_window_end=datetime(2026, 6, 4, 9, 55, tzinfo=UTC)
    )
    dispatcher = FakeTelegramDispatcher()
    service = PriceScheduledAlertEvaluationService(
        alert_repository=alert_repository,
        job_repository=job_repository,
        market_data_service=FakeMarketDataService(
            assets={"bitcoin": _make_price_asset(current_price=105000.0)}
        ),
        telegram_dispatcher=dispatcher,
        clock=lambda: datetime(2026, 6, 4, 10, 0, tzinfo=UTC),
    )

    processed = await service.run_due_windows()

    assert processed == 1
    assert isinstance(service.create_alert_evaluator(), PriceAlertEvaluator)
    assert job_repository.requested_names == [PRICE_ALERT_EVALUATION_CURSOR]
    assert job_repository.advanced_names == [PRICE_ALERT_EVALUATION_CURSOR]
    assert alert_repository.selection_calls == [("price", date(2026, 6, 4))]
    assert len(dispatcher.calls) == 1
    assert dispatcher.calls[0]["event_key"] == f"alert:{alert.id}:one-time:arm:1"
    assert alert.last_triggered_on == date(2026, 6, 4)
    assert alert.status == "paused"


@pytest.mark.asyncio
async def test_price_service_retriggers_recurring_percent_alert_after_rearming() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "price_above",
            "trigger_mode": "percent",
            "threshold_value": 5.0,
            "baseline_price": 100000.0,
            "is_armed": True,
        },
        time_behavior="daily_recurring",
        recurring_start_date=date(2026, 6, 4),
        recurring_end_date=date(2026, 6, 10),
    )
    dispatcher = FakeTelegramDispatcher()
    market_data_service = FakeMarketDataService(
        assets={"bitcoin": _make_price_asset(current_price=105000.0)}
    )
    service = PriceScheduledAlertEvaluationService(
        alert_repository=FakeAlertRepository([alert]),
        job_repository=FakeJobRepository(),
        market_data_service=market_data_service,
        telegram_dispatcher=dispatcher,
        clock=lambda: datetime(2026, 6, 4, 10, 10, tzinfo=UTC),
    )

    first_triggered = await service.run_window(datetime(2026, 6, 4, 10, 0, tzinfo=UTC))
    market_data_service.assets["bitcoin"] = _make_price_asset(current_price=111000.0)
    second_triggered = await service.run_window(datetime(2026, 6, 4, 10, 5, tzinfo=UTC))

    assert first_triggered == 1
    assert second_triggered == 1
    assert len(dispatcher.calls) == 2
    assert dispatcher.calls[0]["event_key"] == f"alert:{alert.id}:window:2026-06-04T10:00:00+00:00"
    assert dispatcher.calls[1]["event_key"] == f"alert:{alert.id}:window:2026-06-04T10:05:00+00:00"
    assert alert.scenario_payload["baseline_price"] == 111000.0
    assert alert.last_triggered_on == date(2026, 6, 4)


@pytest.mark.asyncio
async def test_price_service_rearms_recurring_currency_alert_after_condition_resets() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "price_above",
            "trigger_mode": "currency",
            "threshold_value": 100000.0,
            "is_armed": True,
        },
        time_behavior="daily_recurring",
        recurring_start_date=date(2026, 6, 4),
        recurring_end_date=date(2026, 6, 10),
    )
    dispatcher = FakeTelegramDispatcher()
    market_data_service = FakeMarketDataService(
        assets={"bitcoin": _make_price_asset(current_price=105000.0)}
    )
    service = PriceScheduledAlertEvaluationService(
        alert_repository=FakeAlertRepository([alert]),
        job_repository=FakeJobRepository(),
        market_data_service=market_data_service,
        telegram_dispatcher=dispatcher,
        clock=lambda: datetime(2026, 6, 4, 10, 0, tzinfo=UTC),
    )

    first = await service.run_window(datetime(2026, 6, 4, 10, 0, tzinfo=UTC))
    second = await service.run_window(datetime(2026, 6, 4, 10, 5, tzinfo=UTC))
    market_data_service.assets["bitcoin"] = _make_price_asset(current_price=99000.0)
    third = await service.run_window(datetime(2026, 6, 4, 10, 10, tzinfo=UTC))
    market_data_service.assets["bitcoin"] = _make_price_asset(current_price=106000.0)
    fourth = await service.run_window(datetime(2026, 6, 4, 10, 15, tzinfo=UTC))

    assert first == 1
    assert second == 0
    assert third == 0
    assert fourth == 1
    assert len(dispatcher.calls) == 2
    assert alert.scenario_payload["is_armed"] is False
    assert alert.scenario_payload["threshold_value"] == 106000.0


@pytest.mark.asyncio
async def test_news_service_uses_news_cursor_and_factory_method() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "coin_news",
            "baseline_published_at": "2026-06-04T09:30:00+00:00",
        }
    )
    alert_repository = FakeAlertRepository([alert])
    job_repository = FakeJobRepository(
        last_processed_window_end=datetime(2026, 6, 4, 9, 55, tzinfo=UTC)
    )
    dispatcher = FakeTelegramDispatcher()
    service = NewsScheduledAlertEvaluationService(
        alert_repository=alert_repository,
        job_repository=job_repository,
        market_data_service=FakeMarketDataService(
            news_by_name={
                "Bitcoin": CoinNewsSearchResponse(
                    articles=[
                        {
                            "title": "Bitcoin breaks out",
                            "summary": "Fresh news",
                            "url": "https://example.com/news/1",
                            "image_url": None,
                            "published_at": "2026-06-04T09:45:00+00:00",
                            "source": "Example",
                        }
                    ]
                )
            }
        ),
        telegram_dispatcher=dispatcher,
        clock=lambda: datetime(2026, 6, 4, 10, 0, tzinfo=UTC),
    )

    processed = await service.run_due_windows()

    assert processed == 1
    assert isinstance(service.create_alert_evaluator(), NewsAlertEvaluator)
    assert job_repository.requested_names == [NEWS_ALERT_EVALUATION_CURSOR]
    assert job_repository.advanced_names == [NEWS_ALERT_EVALUATION_CURSOR]
    assert alert_repository.selection_calls == [("news", date(2026, 6, 4))]
    assert len(dispatcher.calls) == 1
    assert dispatcher.calls[0]["title"] == "New coin news for Bitcoin"
    assert alert.scenario_payload["baseline_published_at"] == "2026-06-04T09:45:00+00:00"


@pytest.mark.asyncio
async def test_news_service_emits_multiple_same_day_notifications_for_recurring_alert() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "coin_news",
            "baseline_published_at": "2026-06-04T09:00:00+00:00",
        },
        time_behavior="daily_recurring",
        recurring_start_date=date(2026, 6, 4),
        recurring_end_date=date(2026, 6, 10),
    )
    dispatcher = FakeTelegramDispatcher()
    service = NewsScheduledAlertEvaluationService(
        alert_repository=FakeAlertRepository([alert]),
        job_repository=FakeJobRepository(),
        market_data_service=FakeMarketDataService(
            news_by_name={
                "Bitcoin": CoinNewsSearchResponse(
                    articles=[
                        {
                            "title": "Bitcoin noon update",
                            "summary": "Fresh news",
                            "url": "https://example.com/news/2",
                            "image_url": None,
                            "published_at": "2026-06-04T12:00:00+00:00",
                            "source": "Example",
                        },
                        {
                            "title": "Bitcoin morning update",
                            "summary": "Fresh news",
                            "url": "https://example.com/news/1",
                            "image_url": None,
                            "published_at": "2026-06-04T10:00:00+00:00",
                            "source": "Example",
                        },
                    ]
                )
            }
        ),
        telegram_dispatcher=dispatcher,
        clock=lambda: datetime(2026, 6, 4, 12, 5, tzinfo=UTC),
    )

    triggered = await service.run_window(datetime(2026, 6, 4, 12, 5, tzinfo=UTC))

    assert triggered == 2
    assert len(dispatcher.calls) == 2
    assert dispatcher.calls[0]["body"].startswith("Bitcoin morning update")
    assert dispatcher.calls[1]["body"].startswith("Bitcoin noon update")
    assert alert.scenario_payload["baseline_published_at"] == "2026-06-04T12:00:00+00:00"


@pytest.mark.asyncio
async def test_news_service_catches_up_multiple_same_day_recurring_occurrences() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "coin_news",
            "baseline_published_at": "2026-06-04T09:00:00+00:00",
        },
        time_behavior="daily_recurring",
        recurring_start_date=date(2026, 6, 4),
        recurring_end_date=date(2026, 6, 10),
    )
    dispatcher = FakeTelegramDispatcher()
    service = NewsScheduledAlertEvaluationService(
        alert_repository=FakeAlertRepository([alert]),
        job_repository=FakeJobRepository(
            last_processed_window_end=datetime(2026, 6, 4, 9, 55, tzinfo=UTC)
        ),
        market_data_service=FakeMarketDataService(
            news_sequence=[
                CoinNewsSearchResponse(
                    articles=[
                        {
                            "title": "Bitcoin 10:00 update",
                            "summary": "Fresh news",
                            "url": "https://example.com/news/1",
                            "image_url": None,
                            "published_at": "2026-06-04T10:00:00+00:00",
                            "source": "Example",
                        }
                    ]
                ),
                CoinNewsSearchResponse(
                    articles=[
                        {
                            "title": "Bitcoin 10:05 update",
                            "summary": "Fresh news",
                            "url": "https://example.com/news/2",
                            "image_url": None,
                            "published_at": "2026-06-04T10:05:00+00:00",
                            "source": "Example",
                        },
                        {
                            "title": "Bitcoin 10:00 update",
                            "summary": "Fresh news",
                            "url": "https://example.com/news/1",
                            "image_url": None,
                            "published_at": "2026-06-04T10:00:00+00:00",
                            "source": "Example",
                        },
                    ]
                ),
                CoinNewsSearchResponse(articles=[]),
            ]
        ),
        telegram_dispatcher=dispatcher,
        clock=lambda: datetime(2026, 6, 4, 10, 10, tzinfo=UTC),
    )

    processed = await service.run_due_windows()

    assert processed == 3
    assert len(dispatcher.calls) == 2
    assert dispatcher.calls[0]["body"].startswith("Bitcoin 10:00 update")
    assert dispatcher.calls[1]["body"].startswith("Bitcoin 10:05 update")
    assert alert.scenario_payload["baseline_published_at"] == "2026-06-04T10:05:00+00:00"
