from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.features.alerts.models import AlertRule
from app.features.alerts.schemas import CreateAlertRequest, UpdateAlertRequest
from app.features.alerts.service import AlertService, AlertServiceError
from app.features.auth.models import User
from app.features.market_data.schemas import AssetSearchResultResponse
from app.features.market_data.service import UpstreamMarketDataError


class FakeAlertRepository:
    def __init__(self, alerts: list[AlertRule] | None = None) -> None:
        self.alerts = alerts or []

    async def list_alerts_for_user(self, user_id):
        return [alert for alert in self.alerts if alert.user_id == user_id]

    async def get_alert_for_user(self, user_id, alert_id):
        for alert in self.alerts:
            if alert.user_id == user_id and alert.id == alert_id:
                return alert
        return None

    async def create_alert(self, **kwargs):
        alert = AlertRule(
            id=uuid4(),
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
            status="active",
            **kwargs,
        )
        self.alerts.append(alert)
        return alert

    async def update_alert(self, alert, **kwargs):
        alert.asset_id = kwargs["asset_id"]
        alert.symbol = kwargs["symbol"]
        alert.name = kwargs["name"]
        alert.image_url = kwargs["image_url"]
        alert.time_behavior = kwargs["time_behavior"]
        alert.recurring_start_date = kwargs["recurring_start_date"]
        alert.recurring_end_date = kwargs["recurring_end_date"]
        alert.scenario_payload = kwargs["scenario_payload"]
        alert.updated_at = datetime.now(tz=UTC)
        return alert

    async def set_alert_status(
        self,
        alert,
        status,
    ):
        alert.status = status
        alert.updated_at = datetime.now(tz=UTC)
        return alert

    async def resume_rearmed_one_time_alert(self, alert, *, scenario_payload, arm_version):
        alert.status = "active"
        alert.scenario_payload = scenario_payload
        alert.last_triggered_on = None
        alert.last_triggered_at = None
        alert.arm_version = arm_version
        alert.updated_at = datetime.now(tz=UTC)
        return alert

    async def delete_alert_for_user(self, user_id, alert_id):
        before = len(self.alerts)
        self.alerts = [
            alert
            for alert in self.alerts
            if not (alert.user_id == user_id and alert.id == alert_id)
        ]
        return len(self.alerts) != before


class FakeMarketDataService:
    def __init__(
        self,
        asset: AssetSearchResultResponse | None,
        latest_news_published_at: str | None = None,
        news_error: UpstreamMarketDataError | None = None,
    ) -> None:
        self.asset = asset
        self.latest_news_published_at = latest_news_published_at
        self.news_error = news_error

    async def find_asset(self, *, asset_id: str, symbol: str, name: str):
        if (
            self.asset
            and self.asset.asset_id == asset_id
            and self.asset.symbol == symbol
            and self.asset.name == name
        ):
            return self.asset
        return None

    async def get_coin_news(self, query: str):
        _ = query
        if self.news_error is not None:
            raise self.news_error
        articles = []
        if self.latest_news_published_at is not None:
            articles.append(
                SimpleNamespace(
                    title="Latest news",
                    url="https://example.com/news/latest",
                    published_at=self.latest_news_published_at,
                )
            )
        return SimpleNamespace(articles=articles)


class FakeWatchlistRepository:
    def __init__(self, saved_assets: dict[str, object] | set[str] | None = None) -> None:
        if isinstance(saved_assets, set) or saved_assets is None:
            self.saved_assets = {
                asset_id: SimpleNamespace(
                    asset_id=asset_id,
                    symbol="BTC" if asset_id == "bitcoin" else asset_id.upper(),
                    name="Bitcoin" if asset_id == "bitcoin" else asset_id.title(),
                    image_url="https://example.com/asset.png",
                )
                for asset_id in (saved_assets or set())
            }
        else:
            self.saved_assets = saved_assets

    async def get_asset_for_user(self, user_id, asset_id):
        _ = user_id
        return self.saved_assets.get(asset_id)


def _make_user() -> User:
    return User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="alerts@example.com",
        created_at=datetime.now(tz=UTC),
    )


def _make_asset(asset_id: str = "bitcoin", symbol: str = "BTC", name: str = "Bitcoin"):
    return AssetSearchResultResponse(
        asset_id=asset_id,
        symbol=symbol,
        name=name,
        market_cap_rank=1,
        current_price=100000.0,
        price_change_percentage_24h=2.5,
        image_url="https://example.com/asset.png",
    )


def _make_alert(*, user_id, status: str = "active", asset_id: str = "bitcoin") -> AlertRule:
    return AlertRule(
        id=uuid4(),
        user_id=user_id,
        asset_id=asset_id,
        symbol="BTC",
        name="Bitcoin",
        image_url="https://example.com/asset.png",
        status=status,
        scenario_payload={
            "scenario": "price_above",
            "trigger_mode": "currency",
            "threshold_value": 100000.0,
        },
        time_behavior="one_time",
        recurring_start_date=None,
        recurring_end_date=None,
        arm_version=1,
        last_triggered_on=None,
        last_triggered_at=None,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


@pytest.mark.asyncio
async def test_list_alerts_returns_only_user_owned_items() -> None:
    user = _make_user()
    other_user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(
            [
                _make_alert(user_id=user.id, asset_id="bitcoin"),
                _make_alert(user_id=other_user.id, asset_id="ethereum"),
            ]
        ),
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    response = await service.list_alerts(user)

    assert len(response.items) == 1
    assert response.items[0].asset_id == "bitcoin"
    assert response.items[0].scenario == "price_above"
    assert response.items[0].time_behavior == "one_time"
    assert response.items[0].time_summary == "One-time alert that pauses after it fires"


@pytest.mark.asyncio
async def test_create_alert_captures_percent_baseline() -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    created = await service.create_alert(
        user,
        CreateAlertRequest(
            asset_id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            image_url="https://example.com/asset.png",
            scenario="price_above",
            time_behavior="one_time",
            trigger_mode="percent",
            threshold_value=15,
        ),
    )

    assert created.status == "active"
    assert created.available_actions == ["edit", "pause", "delete"]
    assert created.baseline_price == 100000.0
    assert created.rule_summary == "Price up 15% from baseline"
    assert created.time_behavior == "one_time"
    assert created.time_summary == "One-time alert that pauses after it fires"


@pytest.mark.asyncio
async def test_create_alert_uses_saved_watchlist_asset_metadata() -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository(
            {
                "bitcoin": SimpleNamespace(
                    asset_id="bitcoin",
                    symbol="BTC",
                    name="Bitcoin",
                    image_url="https://example.com/watchlist-bitcoin.png",
                )
            }
        ),
    )

    created = await service.create_alert(
        user,
        CreateAlertRequest(
            asset_id="bitcoin",
            symbol="eth",
            name="Ethereum",
            image_url="https://example.com/ethereum.png",
            scenario="price_above",
            time_behavior="one_time",
            trigger_mode="currency",
            threshold_value=15,
        ),
    )

    assert created.asset_id == "bitcoin"
    assert created.symbol == "BTC"
    assert created.name == "Bitcoin"
    assert created.image_url == "https://example.com/watchlist-bitcoin.png"


@pytest.mark.asyncio
async def test_create_news_alert_does_not_require_trigger_data() -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    created = await service.create_alert(
        user,
        CreateAlertRequest(
            asset_id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            image_url=None,
            scenario="coin_news",
            time_behavior="one_time",
        ),
    )

    assert created.scenario == "coin_news"
    assert created.trigger_mode is None
    assert created.threshold_value is None
    assert created.rule_summary == "Any new coin news"
    assert created.time_summary == "One-time alert that pauses after it fires"


@pytest.mark.asyncio
async def test_create_news_alert_translates_upstream_failure_to_service_error() -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(
            _make_asset(),
            news_error=UpstreamMarketDataError(
                status_code=503,
                message="Market data service is unavailable",
            ),
        ),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    with pytest.raises(AlertServiceError) as exc_info:
        await service.create_alert(
            user,
            CreateAlertRequest(
                asset_id="bitcoin",
                symbol="btc",
                name="Bitcoin",
                image_url=None,
                scenario="coin_news",
                time_behavior="one_time",
            ),
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.message == "Market data service is unavailable"


@pytest.mark.asyncio
async def test_create_alert_requires_current_price_for_percent_rules() -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(None),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    with pytest.raises(AlertServiceError) as exc_info:
        await service.create_alert(
            user,
            CreateAlertRequest(
                asset_id="bitcoin",
                symbol="btc",
                name="Bitcoin",
                image_url=None,
                scenario="price_below",
                time_behavior="one_time",
                trigger_mode="percent",
                threshold_value=10,
            ),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Current price is unavailable for the selected coin"


@pytest.mark.asyncio
async def test_update_alert_replaces_coin_and_recaptures_percent_baseline() -> None:
    user = _make_user()
    existing = AlertRule(
        id=uuid4(),
        user_id=user.id,
        asset_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        image_url="https://example.com/asset.png",
        status="paused",
        scenario_payload={
            "scenario": "price_above",
            "trigger_mode": "percent",
            "threshold_value": 5,
            "baseline_price": 95000.0,
        },
        time_behavior="one_time",
        recurring_start_date=None,
        recurring_end_date=None,
        arm_version=1,
        last_triggered_on=None,
        last_triggered_at=None,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    repository = FakeAlertRepository([existing])
    service = AlertService(
        repository=repository,
        market_data_service=FakeMarketDataService(_make_asset("ethereum", "ETH", "Ethereum")),
        watchlist_repository=FakeWatchlistRepository(
            {
                "bitcoin": SimpleNamespace(
                    asset_id="bitcoin",
                    symbol="BTC",
                    name="Bitcoin",
                    image_url="https://example.com/asset.png",
                ),
                "ethereum": SimpleNamespace(
                    asset_id="ethereum",
                    symbol="ETH",
                    name="Ethereum",
                    image_url="https://example.com/asset.png",
                ),
            }
        ),
    )

    updated = await service.update_alert(
        user,
        existing.id,
        UpdateAlertRequest(
            asset_id="ethereum",
            symbol="eth",
            name="Ethereum",
            image_url=None,
            scenario="price_below",
            time_behavior="one_time",
            trigger_mode="percent",
            threshold_value=8,
        ),
    )

    assert updated.asset_id == "ethereum"
    assert updated.status == "paused"
    assert updated.scenario == "price_below"
    assert updated.baseline_price == 100000.0
    assert updated.time_summary == "One-time alert that pauses after it fires"


@pytest.mark.asyncio
async def test_create_alert_requires_selected_coin_in_watchlist() -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository(),
    )

    with pytest.raises(AlertServiceError) as exc_info:
        await service.create_alert(
            user,
            CreateAlertRequest(
                asset_id="bitcoin",
                symbol="btc",
                name="Bitcoin",
                image_url=None,
                scenario="price_above",
                time_behavior="one_time",
                trigger_mode="currency",
                threshold_value=100000,
            ),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Selected coin must be saved in your watchlist"


@pytest.mark.asyncio
async def test_pause_resume_and_delete_alert() -> None:
    user = _make_user()
    existing = _make_alert(user_id=user.id)
    repository = FakeAlertRepository([existing])
    service = AlertService(
        repository=repository,
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    paused = await service.pause_alert(user, existing.id)
    resumed = await service.resume_alert(user, existing.id)
    deleted = await service.delete_alert(user, existing.id)

    assert paused.status == "paused"
    assert paused.available_actions == ["edit", "resume", "delete"]
    assert resumed.status == "active"
    assert deleted.success is True
    assert repository.alerts == []


@pytest.mark.asyncio
async def test_resume_triggered_one_time_percent_alert_rearms_from_current_price() -> None:
    user = _make_user()
    existing = _make_alert(user_id=user.id, status="paused")
    existing.scenario_payload = {
        "scenario": "price_above",
        "trigger_mode": "percent",
        "threshold_value": 5.0,
        "baseline_price": 95000.0,
        "is_armed": False,
    }
    existing.last_triggered_on = date(2026, 6, 9)
    existing.last_triggered_at = datetime(2026, 6, 9, 12, 0, tzinfo=UTC)
    existing.arm_version = 2
    repository = FakeAlertRepository([existing])
    service = AlertService(
        repository=repository,
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    resumed = await service.resume_alert(user, existing.id)

    assert resumed.status == "active"
    assert existing.scenario_payload["baseline_price"] == 100000.0
    assert existing.scenario_payload["is_armed"] is True
    assert existing.last_triggered_on is None
    assert existing.last_triggered_at is None
    assert existing.arm_version == 3


@pytest.mark.asyncio
async def test_resume_triggered_one_time_currency_alert_rearms_from_current_price() -> None:
    user = _make_user()
    existing = _make_alert(user_id=user.id, status="paused")
    existing.scenario_payload = {
        "scenario": "price_above",
        "trigger_mode": "currency",
        "threshold_value": 95000.0,
        "is_armed": False,
    }
    existing.last_triggered_on = date(2026, 6, 9)
    existing.last_triggered_at = datetime(2026, 6, 9, 12, 0, tzinfo=UTC)
    repository = FakeAlertRepository([existing])
    service = AlertService(
        repository=repository,
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    resumed = await service.resume_alert(user, existing.id)

    assert resumed.status == "active"
    assert existing.scenario_payload["threshold_value"] == 100000.0
    assert existing.scenario_payload["is_armed"] is True
    assert existing.last_triggered_on is None
    assert existing.last_triggered_at is None


@pytest.mark.asyncio
async def test_resume_triggered_one_time_news_alert_rearms_from_current_news_state() -> None:
    user = _make_user()
    existing = _make_alert(user_id=user.id, status="paused")
    existing.scenario_payload = {
        "scenario": "coin_news",
        "baseline_published_at": "2026-06-09T08:00:00+00:00",
    }
    existing.last_triggered_on = date(2026, 6, 9)
    existing.last_triggered_at = datetime(2026, 6, 9, 12, 0, tzinfo=UTC)
    repository = FakeAlertRepository([existing])
    service = AlertService(
        repository=repository,
        market_data_service=FakeMarketDataService(
            _make_asset(),
            latest_news_published_at="2026-06-09T12:30:00+00:00",
        ),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    resumed = await service.resume_alert(user, existing.id)

    assert resumed.status == "active"
    assert existing.scenario_payload["baseline_published_at"] == "2026-06-09T12:30:00+00:00"
    assert existing.last_triggered_at is None


@pytest.mark.asyncio
async def test_resume_triggered_one_time_news_alert_uses_newest_visible_article() -> None:
    user = _make_user()
    existing = _make_alert(user_id=user.id, status="paused")
    existing.scenario_payload = {
        "scenario": "coin_news",
        "baseline_published_at": "2026-06-09T08:00:00+00:00",
    }
    existing.last_triggered_on = date(2026, 6, 9)
    existing.last_triggered_at = datetime(2026, 6, 9, 12, 0, tzinfo=UTC)
    repository = FakeAlertRepository([existing])
    service = AlertService(
        repository=repository,
        market_data_service=FakeMarketDataService(
            _make_asset(),
            latest_news_published_at="2026-06-09T12:30:00+00:00",
        ),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    async def _get_coin_news(query: str):
        _ = query
        return SimpleNamespace(
            articles=[
                SimpleNamespace(
                    title="Older",
                    url="https://example.com/news/older",
                    published_at="2026-06-09T10:00:00+00:00",
                ),
                SimpleNamespace(
                    title="Newest",
                    url="https://example.com/news/newest",
                    published_at="2026-06-09T12:30:00+00:00",
                ),
            ]
        )

    service.market_data_service.get_coin_news = _get_coin_news  # type: ignore[method-assign]

    await service.resume_alert(user, existing.id)

    assert existing.scenario_payload["baseline_published_at"] == "2026-06-09T12:30:00+00:00"


@pytest.mark.asyncio
async def test_update_alert_rejects_missing_user_owned_record() -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    with pytest.raises(AlertServiceError) as exc_info:
        await service.update_alert(
            user,
            uuid4(),
            UpdateAlertRequest(
                asset_id="bitcoin",
                symbol="btc",
                name="Bitcoin",
                image_url=None,
                scenario="price_above",
                time_behavior="one_time",
                trigger_mode="currency",
                threshold_value=100000,
            ),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Alert not found"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("operation_name", "operation"),
    [
        ("pause", lambda service, user, alert_id: service.pause_alert(user, alert_id)),
        ("resume", lambda service, user, alert_id: service.resume_alert(user, alert_id)),
        ("delete", lambda service, user, alert_id: service.delete_alert(user, alert_id)),
    ],
)
async def test_alert_operations_reject_missing_user_owned_record(
    operation_name: str,
    operation,
) -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    with pytest.raises(AlertServiceError) as exc_info:
        await operation(service, user, uuid4())

    assert exc_info.value.status_code == 404, operation_name
    assert exc_info.value.message == "Alert not found"


def test_create_alert_rejects_invalid_recurring_window() -> None:
    with pytest.raises(
        ValueError,
        match="Recurring alert end date must be on or after the start date",
    ):
        CreateAlertRequest(
            asset_id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            image_url=None,
            scenario="coin_news",
            time_behavior="daily_recurring",
            recurring_start_date=date(2026, 5, 27),
            recurring_end_date=date(2026, 5, 20),
        )


@pytest.mark.asyncio
async def test_create_alert_returns_recurring_time_summary() -> None:
    user = _make_user()
    service = AlertService(
        repository=FakeAlertRepository(),
        market_data_service=FakeMarketDataService(_make_asset()),
        watchlist_repository=FakeWatchlistRepository({"bitcoin"}),
    )

    created = await service.create_alert(
        user,
        CreateAlertRequest(
            asset_id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            image_url=None,
            scenario="coin_news",
            time_behavior="daily_recurring",
            recurring_start_date=date(2026, 5, 27),
            recurring_end_date=date(2026, 6, 3),
        ),
    )

    assert created.time_behavior == "daily_recurring"
    assert created.recurring_start_date == date(2026, 5, 27)
    assert created.recurring_end_date == date(2026, 6, 3)
    assert created.time_summary == "Recurring from 2026-05-27 to 2026-06-03"
