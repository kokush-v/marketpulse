from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from app.features.alerts.models import AlertRule
from app.features.alerts.repository import AlertRepository
from app.features.background_jobs.repository import BackgroundJobRepository
from app.features.market_data.service import MarketDataService
from app.features.telegram.service import TelegramNotificationDispatcher

logger = logging.getLogger("uvicorn.error")

ALERT_EVALUATION_CURSOR = "scheduled_alert_evaluation"
ALERT_EVALUATION_CADENCE = timedelta(minutes=5)


@dataclass
class TriggeredAlertPayload:
    title: str
    body: str
    event_key: str
    next_scenario_payload: dict[str, object] | None = None


class ScheduledAlertEvaluationService:
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

    async def run_due_windows(self) -> int:
        current_window_end = self._align_window_end(self.clock())
        cursor = await self.job_repository.get_cursor(ALERT_EVALUATION_CURSOR)
        if cursor is None:
            cursor = await self.job_repository.ensure_cursor(
                name=ALERT_EVALUATION_CURSOR,
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
                name=ALERT_EVALUATION_CURSOR,
                last_processed_window_end=next_window_end,
            )
            processed_windows += 1
            next_window_end += ALERT_EVALUATION_CADENCE

        return processed_windows

    async def run_window(self, window_end: datetime) -> int:
        eligible_alerts = await self.alert_repository.list_eligible_alerts_for_window(
            window_end.date()
        )
        triggered_count = 0
        for alert in eligible_alerts:
            trigger_payload = await self._build_trigger_payload(alert, window_end)
            if trigger_payload is None:
                continue

            logger.info(
                "[%s] Trigger for alert %s type %s user %s window %s",
                self.clock().isoformat(),
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
            await self.alert_repository.update_evaluation_state(
                alert,
                last_triggered_on=window_end.date(),
                scenario_payload=trigger_payload.next_scenario_payload,
            )
            triggered_count += 1

        if triggered_count:
            logger.info(
                "Processed %s triggered alerts for evaluation window ending %s",
                triggered_count,
                window_end.isoformat(),
            )
        return triggered_count

    async def _build_trigger_payload(
        self,
        alert: AlertRule,
        window_end: datetime,
    ) -> TriggeredAlertPayload | None:
        scenario = str(alert.scenario_payload["scenario"])
        if scenario == "coin_news":
            return await self._build_news_trigger_payload(alert, window_end)
        return await self._build_price_trigger_payload(alert, window_end)

    async def _build_price_trigger_payload(
        self,
        alert: AlertRule,
        window_end: datetime,
    ) -> TriggeredAlertPayload | None:
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
            return None

        comparator = "above" if scenario == "price_above" else "below"
        event_key = self._build_event_key(alert.id, alert.time_behavior, window_end.date())
        return TriggeredAlertPayload(
            title=f"{alert.name} alert triggered",
            body=(
                f"{alert.name} ({alert.symbol}) moved {comparator} "
                f"{self._format_threshold(trigger_mode, threshold_value, target_price)}. "
                f"Latest price: ${current_price:,.2f}."
            ),
            event_key=event_key,
        )

    async def _build_news_trigger_payload(
        self,
        alert: AlertRule,
        window_end: datetime,
    ) -> TriggeredAlertPayload | None:
        articles = await self.market_data_service.get_coin_news(alert.name)
        baseline_iso = str(alert.scenario_payload.get("baseline_published_at", "")).strip()
        baseline = self._parse_iso_datetime(baseline_iso)

        fresh_articles = [
            article
            for article in articles.articles
            if article.published_at and self._is_new_article(article.published_at, baseline)
        ]
        if not fresh_articles:
            return None

        latest_article = fresh_articles[0]
        next_payload = dict(alert.scenario_payload)
        next_payload["baseline_published_at"] = latest_article.published_at
        event_key = self._build_event_key(alert.id, alert.time_behavior, window_end.date())
        return TriggeredAlertPayload(
            title=f"New coin news for {alert.name}",
            body=(f"{latest_article.title}\n{latest_article.url}"),
            event_key=event_key,
            next_scenario_payload=next_payload,
        )

    def _align_window_end(self, value: datetime) -> datetime:
        normalized = value.astimezone(UTC).replace(second=0, microsecond=0)
        minute = normalized.minute - (normalized.minute % 5)
        return normalized.replace(minute=minute)

    def _build_event_key(self, alert_id: UUID, time_behavior: str, window_date: date) -> str:
        if time_behavior == "daily_recurring":
            return f"alert:{alert_id}:day:{window_date.isoformat()}"
        return f"alert:{alert_id}:one-time"

    def _format_threshold(
        self,
        trigger_mode: str,
        threshold_value: float,
        target_price: float,
    ) -> str:
        if trigger_mode == "percent":
            return f"{threshold_value:g}% from baseline (${target_price:,.2f})"
        return f"${target_price:,.2f}"

    def _parse_iso_datetime(self, value: str) -> datetime | None:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)

    def _is_new_article(self, published_at: str, baseline: datetime | None) -> bool:
        published = self._parse_iso_datetime(published_at)
        if published is None:
            return False
        if baseline is None:
            return True
        return published > baseline
