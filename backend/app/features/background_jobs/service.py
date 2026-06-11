from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha1

from app.features.alerts.models import AlertRule
from app.features.alerts.repository import AlertRepository
from app.features.background_jobs.repository import BackgroundJobRepository
from app.features.market_data.service import MarketDataService
from app.features.telegram.service import TelegramNotificationDispatcher

logger = logging.getLogger("uvicorn.error")

PRICE_ALERT_EVALUATION_CURSOR = "scheduled_price_alert_evaluation"
NEWS_ALERT_EVALUATION_CURSOR = "scheduled_news_alert_evaluation"
ALERT_EVALUATION_CADENCE = timedelta(minutes=5)


@dataclass
class TriggeredAlertPayload:
    title: str
    body: str
    event_key: str
    next_scenario_payload: dict[str, object]


@dataclass
class AlertEvaluationResult:
    trigger_payloads: list[TriggeredAlertPayload]
    next_scenario_payload: dict[str, object] | None = None


class AlertEvaluator(ABC):
    @abstractmethod
    async def evaluate(
        self,
        alert: AlertRule,
        window_end: datetime,
    ) -> AlertEvaluationResult: ...


class PriceAlertEvaluator(AlertEvaluator):
    def __init__(self, *, market_data_service: MarketDataService) -> None:
        self.market_data_service = market_data_service

    async def evaluate(
        self,
        alert: AlertRule,
        window_end: datetime,
    ) -> AlertEvaluationResult:
        asset = await self.market_data_service.find_asset(
            asset_id=alert.asset_id,
            symbol=alert.symbol,
            name=alert.name,
        )
        if asset is None:
            raise RuntimeError(f"Current price is unavailable for alert {alert.id}")

        current_price = float(asset.current_price)
        scenario = str(alert.scenario_payload["scenario"])
        threshold_value = float(alert.scenario_payload["threshold_value"])
        trigger_mode = str(alert.scenario_payload["trigger_mode"])
        is_armed = bool(alert.scenario_payload.get("is_armed", True))

        if trigger_mode == "percent":
            baseline_price = float(alert.scenario_payload["baseline_price"])
            multiplier = (
                1 + (threshold_value / 100)
                if scenario == "price_above"
                else 1 - (threshold_value / 100)
            )
            target_price = baseline_price * multiplier
        else:
            target_price = threshold_value

        is_triggered = current_price >= target_price
        if scenario != "price_above":
            is_triggered = current_price <= target_price
        if not is_triggered:
            if alert.time_behavior == "daily_recurring" and not is_armed:
                next_payload = dict(alert.scenario_payload)
                next_payload["is_armed"] = True
                return AlertEvaluationResult(
                    trigger_payloads=[],
                    next_scenario_payload=next_payload,
                )
            return AlertEvaluationResult(trigger_payloads=[])

        if alert.time_behavior == "daily_recurring" and not is_armed:
            return AlertEvaluationResult(trigger_payloads=[])

        comparator = "above" if scenario == "price_above" else "below"
        next_payload = dict(alert.scenario_payload)
        if alert.time_behavior == "daily_recurring":
            if trigger_mode == "percent":
                next_payload["baseline_price"] = current_price
                next_payload["is_armed"] = True
            else:
                next_payload["threshold_value"] = current_price
                next_payload["is_armed"] = False

        return AlertEvaluationResult(
            trigger_payloads=[
                TriggeredAlertPayload(
                    title=f"{alert.name} alert triggered",
                    body=(
                        f"{alert.name} ({alert.symbol}) moved {comparator} "
                        f"{self._format_threshold(trigger_mode, threshold_value, target_price)}. "
                        f"Latest price: ${current_price:,.2f}."
                    ),
                    event_key=self._build_event_key(alert, window_end),
                    next_scenario_payload=next_payload,
                )
            ]
        )

    def _build_event_key(self, alert: AlertRule, window_end: datetime) -> str:
        if alert.time_behavior == "one_time":
            return f"alert:{alert.id}:one-time:arm:{alert.arm_version}"
        return f"alert:{alert.id}:window:{window_end.astimezone(UTC).isoformat()}"

    def _format_threshold(
        self,
        trigger_mode: str,
        threshold_value: float,
        target_price: float,
    ) -> str:
        if trigger_mode == "percent":
            return f"{threshold_value:g}% from baseline (${target_price:,.2f})"
        return f"${target_price:,.2f}"


class NewsAlertEvaluator(AlertEvaluator):
    def __init__(self, *, market_data_service: MarketDataService) -> None:
        self.market_data_service = market_data_service

    async def evaluate(
        self,
        alert: AlertRule,
        window_end: datetime,
    ) -> AlertEvaluationResult:
        _ = window_end
        articles = await self.market_data_service.get_coin_news(alert.name)
        baseline_iso = str(alert.scenario_payload.get("baseline_published_at", "")).strip()
        baseline = self._parse_iso_datetime(baseline_iso)

        fresh_articles = [
            article
            for article in articles.articles
            if article.published_at and self._is_new_article(article.published_at, baseline)
        ]
        if not fresh_articles:
            return AlertEvaluationResult(trigger_payloads=[])

        sorted_articles = sorted(
            fresh_articles,
            key=lambda article: (
                self._parse_iso_datetime(article.published_at or "")
                or datetime.min.replace(tzinfo=UTC)
            ),
        )
        if alert.time_behavior == "one_time":
            sorted_articles = [sorted_articles[-1]]

        trigger_payloads: list[TriggeredAlertPayload] = []
        next_payload = dict(alert.scenario_payload)
        for article in sorted_articles:
            next_payload = dict(next_payload)
            next_payload["baseline_published_at"] = article.published_at
            trigger_payloads.append(
                TriggeredAlertPayload(
                    title=f"New coin news for {alert.name}",
                    body=f"{article.title}\n{article.url}",
                    event_key=self._build_event_key(alert, article),
                    next_scenario_payload=next_payload,
                )
            )

        return AlertEvaluationResult(trigger_payloads=trigger_payloads)

    def _build_event_key(self, alert: AlertRule, article) -> str:
        article_fingerprint = sha1(
            f"{article.url}|{article.published_at or ''}".encode()
        ).hexdigest()
        if alert.time_behavior == "one_time":
            return f"alert:{alert.id}:one-time:arm:{alert.arm_version}:{article_fingerprint}"
        return f"alert:{alert.id}:news:{article_fingerprint}"

    def _parse_iso_datetime(self, value: str) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _is_new_article(self, published_at: str, baseline: datetime | None) -> bool:
        published = self._parse_iso_datetime(published_at)
        if published is None:
            return False
        if baseline is None:
            return True
        return published > baseline


class BaseScheduledAlertEvaluationService(ABC):
    def __init__(
        self,
        *,
        alert_repository: AlertRepository,
        job_repository: BackgroundJobRepository,
        market_data_service: MarketDataService,
        telegram_dispatcher: TelegramNotificationDispatcher,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.alert_repository = alert_repository
        self.job_repository = job_repository
        self.market_data_service = market_data_service
        self.telegram_dispatcher = telegram_dispatcher
        self.clock = clock or (lambda: datetime.now(tz=UTC))

    @property
    @abstractmethod
    def cursor_name(self) -> str: ...

    @property
    @abstractmethod
    def job_name(self) -> str: ...

    @abstractmethod
    async def list_eligible_alerts(self, window_end: datetime) -> list[AlertRule]: ...

    @abstractmethod
    def create_alert_evaluator(self) -> AlertEvaluator: ...

    async def run_due_windows(self) -> int:
        current_window_end = self._align_window_end(self.clock())
        cursor = await self.job_repository.get_cursor(self.cursor_name)
        if cursor is None:
            cursor = await self.job_repository.ensure_cursor(
                name=self.cursor_name,
                default_last_processed_window_end=current_window_end - ALERT_EVALUATION_CADENCE,
            )

        if cursor.last_processed_window_end is None:
            next_window_end = current_window_end
        else:
            next_window_end = cursor.last_processed_window_end + ALERT_EVALUATION_CADENCE

        processed_windows = 0
        while next_window_end <= current_window_end:
            await self.run_window(next_window_end)
            await self.job_repository.advance_cursor(
                name=self.cursor_name,
                last_processed_window_end=next_window_end,
            )
            processed_windows += 1
            next_window_end += ALERT_EVALUATION_CADENCE

        return processed_windows

    async def run_window(self, window_end: datetime) -> int:
        eligible_alerts = await self.list_eligible_alerts(window_end)
        evaluator = self.create_alert_evaluator()
        triggered_count = 0

        for alert in eligible_alerts:
            evaluation_result = await evaluator.evaluate(alert, window_end)
            if not evaluation_result.trigger_payloads:
                if evaluation_result.next_scenario_payload is not None:
                    await self.alert_repository.update_alert_runtime_state(
                        alert,
                        scenario_payload=evaluation_result.next_scenario_payload,
                    )
                continue

            for trigger_payload in evaluation_result.trigger_payloads:
                logger.info(
                    "[%s] Trigger for %s alert %s type %s user %s window %s",
                    self.clock().isoformat(),
                    self.job_name,
                    alert.id,
                    alert.scenario_payload["scenario"],
                    alert.user_id,
                    window_end.isoformat(),
                )

                await self.telegram_dispatcher.dispatch_scheduled_alert_notification(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    title=trigger_payload.title,
                    body=trigger_payload.body,
                    event_key=trigger_payload.event_key,
                    event_timestamp=window_end,
                )
                await self.alert_repository.record_trigger_result(
                    alert,
                    triggered_at=window_end,
                    scenario_payload=trigger_payload.next_scenario_payload,
                    pause_after_trigger=alert.time_behavior == "one_time",
                )
                triggered_count += 1

        if triggered_count:
            logger.info(
                "Processed %s triggered %s alert(s) for evaluation window ending %s",
                triggered_count,
                self.job_name,
                window_end.isoformat(),
            )
        return triggered_count

    def _align_window_end(self, value: datetime) -> datetime:
        normalized = value.astimezone(UTC).replace(second=0, microsecond=0)
        minute = normalized.minute - (normalized.minute % 5)
        return normalized.replace(minute=minute)


class PriceScheduledAlertEvaluationService(BaseScheduledAlertEvaluationService):
    @property
    def cursor_name(self) -> str:
        return PRICE_ALERT_EVALUATION_CURSOR

    @property
    def job_name(self) -> str:
        return "price"

    async def list_eligible_alerts(self, window_end: datetime) -> list[AlertRule]:
        return await self.alert_repository.list_eligible_price_alerts_for_window(window_end.date())

    def create_alert_evaluator(self) -> AlertEvaluator:
        return PriceAlertEvaluator(market_data_service=self.market_data_service)


class NewsScheduledAlertEvaluationService(BaseScheduledAlertEvaluationService):
    @property
    def cursor_name(self) -> str:
        return NEWS_ALERT_EVALUATION_CURSOR

    @property
    def job_name(self) -> str:
        return "news"

    async def list_eligible_alerts(self, window_end: datetime) -> list[AlertRule]:
        return await self.alert_repository.list_eligible_news_alerts_for_window(window_end.date())

    def create_alert_evaluator(self) -> AlertEvaluator:
        return NewsAlertEvaluator(market_data_service=self.market_data_service)
