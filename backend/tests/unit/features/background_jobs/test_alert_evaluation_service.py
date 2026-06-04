from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.features.alerts.models import AlertRule
from app.features.background_jobs.service import ScheduledAlertEvaluationService
from app.features.market_data.schemas import AssetSearchResultResponse, CoinNewsSearchResponse


class FakeAlertRepository:
    def __init__(self, alerts: list[AlertRule]) -> None:
        self.alerts = alerts

    async def list_eligible_alerts_for_window(self, window_date: date) -> list[AlertRule]:
        eligible: list[AlertRule] = []
        for alert in self.alerts:
            if alert.status != "active":
                continue
            if alert.time_behavior == "one_time":
                if alert.last_triggered_on is None:
                    eligible.append(alert)
                continue

            if (
                alert.recurring_start_date is None
                or alert.recurring_end_date is None
                or alert.recurring_start_date > window_date
                or alert.recurring_end_date < window_date
            ):
                continue
            if alert.last_triggered_on is not None and alert.last_triggered_on >= window_date:
                continue
            eligible.append(alert)
        return eligible

    async def update_evaluation_state(
        self,
        alert: AlertRule,
        *,
        last_triggered_on: date,
        scenario_payload: dict[str, object] | None = None,
        commit: bool = True,
    ) -> AlertRule:
        _ = commit
        alert.last_triggered_on = last_triggered_on
        if scenario_payload is not None:
            alert.scenario_payload = scenario_payload
        return alert


class FakeJobRepository:
    def __init__(self, last_processed_window_end: datetime | None = None) -> None:
        self.cursor = SimpleNamespace(
            name="scheduled_alert_evaluation",
            last_processed_window_end=last_processed_window_end,
        )

    async def get_cursor(self, name: str):
        _ = name
        return self.cursor

    async def ensure_cursor(self, *, name: str, default_last_processed_window_end: datetime | None):
        self.cursor = SimpleNamespace(
            name=name,
            last_processed_window_end=default_last_processed_window_end,
        )
        return self.cursor

    async def advance_cursor(self, *, name: str, last_processed_window_end: datetime):
        _ = name
        self.cursor.last_processed_window_end = last_processed_window_end
        return self.cursor


class FakeMarketDataService:
    def __init__(
        self,
        *,
        assets: dict[str, AssetSearchResultResponse] | None = None,
        news_by_name: dict[str, CoinNewsSearchResponse] | None = None,
    ) -> None:
        self.assets = assets or {}
        self.news_by_name = news_by_name or {}

    async def find_asset(self, *, asset_id: str, symbol: str, name: str):
        _ = symbol, name
        return self.assets.get(asset_id)

    async def get_coin_news(self, query: str) -> CoinNewsSearchResponse:
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
        last_triggered_on=last_triggered_on,
        scenario_payload=scenario_payload,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


@pytest.mark.asyncio
async def test_run_due_windows_processes_one_time_price_alert_once() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "price_above",
            "trigger_mode": "currency",
            "threshold_value": 100000.0,
        }
    )
    dispatcher = FakeTelegramDispatcher()
    service = ScheduledAlertEvaluationService(
        alert_repository=FakeAlertRepository([alert]),
        job_repository=FakeJobRepository(
            last_processed_window_end=datetime(2026, 6, 4, 9, 55, tzinfo=UTC)
        ),
        market_data_service=FakeMarketDataService(
            assets={"bitcoin": _make_price_asset(current_price=105000.0)}
        ),
        telegram_dispatcher=dispatcher,
        clock=lambda: datetime(2026, 6, 4, 10, 0, tzinfo=UTC),
    )

    processed = await service.run_due_windows()

    assert processed == 1
    assert len(dispatcher.calls) == 1
    assert dispatcher.calls[0]["event_key"] == f"alert:{alert.id}:one-time"
    assert alert.last_triggered_on == date(2026, 6, 4)


@pytest.mark.asyncio
async def test_run_due_windows_catches_up_missed_windows_without_duplicate_daily_trigger() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "price_above",
            "trigger_mode": "currency",
            "threshold_value": 100000.0,
        },
        time_behavior="daily_recurring",
        recurring_start_date=date(2026, 6, 4),
        recurring_end_date=date(2026, 6, 10),
    )
    dispatcher = FakeTelegramDispatcher()
    service = ScheduledAlertEvaluationService(
        alert_repository=FakeAlertRepository([alert]),
        job_repository=FakeJobRepository(
            last_processed_window_end=datetime(2026, 6, 4, 9, 55, tzinfo=UTC)
        ),
        market_data_service=FakeMarketDataService(
            assets={"bitcoin": _make_price_asset(current_price=110000.0)}
        ),
        telegram_dispatcher=dispatcher,
        clock=lambda: datetime(2026, 6, 4, 10, 10, tzinfo=UTC),
    )

    processed = await service.run_due_windows()

    assert processed == 3
    assert len(dispatcher.calls) == 1
    assert dispatcher.calls[0]["event_key"] == f"alert:{alert.id}:day:2026-06-04"
    assert alert.last_triggered_on == date(2026, 6, 4)


@pytest.mark.asyncio
async def test_run_window_updates_news_baseline_after_trigger() -> None:
    alert = _make_alert(
        scenario_payload={
            "scenario": "coin_news",
            "baseline_published_at": "2026-06-04T09:30:00+00:00",
        }
    )
    dispatcher = FakeTelegramDispatcher()
    service = ScheduledAlertEvaluationService(
        alert_repository=FakeAlertRepository([alert]),
        job_repository=FakeJobRepository(),
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

    triggered = await service.run_window(datetime(2026, 6, 4, 10, 0, tzinfo=UTC))

    assert triggered == 1
    assert len(dispatcher.calls) == 1
    assert dispatcher.calls[0]["title"] == "New coin news for Bitcoin"
    assert alert.scenario_payload["baseline_published_at"] == "2026-06-04T09:45:00+00:00"
