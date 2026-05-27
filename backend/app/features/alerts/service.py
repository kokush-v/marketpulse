from __future__ import annotations

from datetime import date
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.features.alerts.models import AlertRule
from app.features.alerts.repository import AlertRepository
from app.features.alerts.schemas import (
    AlertListResponse,
    AlertOperationResponse,
    AlertResponse,
    AlertScenario,
    AlertTimeBehavior,
    CreateAlertRequest,
    TriggerMode,
    UpdateAlertRequest,
)
from app.features.auth.models import User
from app.features.market_data.service import MarketDataService
from app.features.watchlists.repository import WatchlistRepository
from app.features.watchlists.service import get_watchlist_repository


def get_alert_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AlertRepository:
    return AlertRepository(session)


class AlertServiceError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class AlertService:
    def __init__(
        self,
        repository: Annotated[AlertRepository, Depends(get_alert_repository)],
        market_data_service: Annotated[MarketDataService, Depends()],
        watchlist_repository: Annotated[WatchlistRepository, Depends(get_watchlist_repository)],
    ) -> None:
        self.repository = repository
        self.market_data_service = market_data_service
        self.watchlist_repository = watchlist_repository

    async def list_alerts(self, user: User) -> AlertListResponse:
        alerts = await self.repository.list_alerts_for_user(user.id)
        return AlertListResponse(items=[self._to_response(alert) for alert in alerts])

    async def create_alert(self, user: User, payload: CreateAlertRequest) -> AlertResponse:
        normalized = await self._normalize_payload(user, payload)
        alert = await self.repository.create_alert(user_id=user.id, **normalized)
        return self._to_response(alert)

    async def update_alert(
        self,
        user: User,
        alert_id: UUID,
        payload: UpdateAlertRequest,
    ) -> AlertResponse:
        alert = await self.repository.get_alert_for_user(user.id, alert_id)
        if alert is None:
            raise AlertServiceError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Alert not found",
            )

        normalized = await self._normalize_payload(user, payload)
        updated = await self.repository.update_alert(alert, **normalized)
        return self._to_response(updated)

    async def pause_alert(self, user: User, alert_id: UUID) -> AlertResponse:
        alert = await self.repository.get_alert_for_user(user.id, alert_id)
        if alert is None:
            raise AlertServiceError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Alert not found",
            )
        paused = await self.repository.set_alert_status(alert, "paused")
        return self._to_response(paused)

    async def resume_alert(self, user: User, alert_id: UUID) -> AlertResponse:
        alert = await self.repository.get_alert_for_user(user.id, alert_id)
        if alert is None:
            raise AlertServiceError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Alert not found",
            )
        resumed = await self.repository.set_alert_status(alert, "active")
        return self._to_response(resumed)

    async def delete_alert(self, user: User, alert_id: UUID) -> AlertOperationResponse:
        deleted = await self.repository.delete_alert_for_user(user.id, alert_id)
        if not deleted:
            raise AlertServiceError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Alert not found",
            )
        return AlertOperationResponse(success=True)

    async def _normalize_payload(
        self,
        user: User,
        payload: CreateAlertRequest | UpdateAlertRequest,
    ) -> dict[str, object]:
        asset_id = payload.asset_id.strip().lower()

        saved_asset = await self.watchlist_repository.get_asset_for_user(user.id, asset_id)
        if saved_asset is None:
            raise AlertServiceError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                message="Selected coin must be saved in your watchlist",
            )

        normalized_asset_id = saved_asset.asset_id.strip().lower()
        normalized_symbol = saved_asset.symbol.strip().upper()
        normalized_name = saved_asset.name.strip()
        normalized_image_url = saved_asset.image_url.strip() if saved_asset.image_url else None

        scenario_payload = await self._normalize_scenario_payload(
            asset_id=normalized_asset_id,
            symbol=normalized_symbol,
            name=normalized_name,
            scenario=payload.scenario,
            trigger_mode=payload.trigger_mode,
            threshold_value=payload.threshold_value,
        )
        return {
            "asset_id": normalized_asset_id,
            "symbol": normalized_symbol,
            "name": normalized_name,
            "image_url": normalized_image_url,
            "time_behavior": payload.time_behavior,
            "recurring_start_date": payload.recurring_start_date,
            "recurring_end_date": payload.recurring_end_date,
            "scenario_payload": scenario_payload,
        }

    async def _normalize_scenario_payload(
        self,
        *,
        asset_id: str,
        symbol: str,
        name: str,
        scenario: AlertScenario,
        trigger_mode: TriggerMode | None,
        threshold_value: float | None,
    ) -> dict[str, object]:
        if scenario == "coin_news":
            return {"scenario": scenario}

        if trigger_mode is None or threshold_value is None:
            raise AlertServiceError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                message="Price alerts require trigger mode and threshold value",
            )

        payload: dict[str, object] = {
            "scenario": scenario,
            "trigger_mode": trigger_mode,
            "threshold_value": float(threshold_value),
        }

        if trigger_mode == "percent":
            payload["baseline_price"] = await self._resolve_current_price(
                asset_id=asset_id,
                symbol=symbol,
                name=name,
            )

        return payload

    async def _resolve_current_price(self, *, asset_id: str, symbol: str, name: str) -> float:
        asset = await self.market_data_service.find_asset(
            asset_id=asset_id,
            symbol=symbol,
            name=name,
        )
        if asset is None:
            raise AlertServiceError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                message="Current price is unavailable for the selected coin",
            )
        return float(asset.current_price)

    def _to_response(self, alert: AlertRule) -> AlertResponse:
        scenario_payload = alert.scenario_payload
        return AlertResponse(
            id=alert.id,
            asset_id=alert.asset_id,
            symbol=alert.symbol,
            name=alert.name,
            image_url=alert.image_url,
            status="active" if alert.status == "active" else "paused",
            scenario=str(scenario_payload["scenario"]),
            time_behavior=cast(AlertTimeBehavior, alert.time_behavior),
            recurring_start_date=alert.recurring_start_date,
            recurring_end_date=alert.recurring_end_date,
            trigger_mode=scenario_payload.get("trigger_mode"),
            threshold_value=self._float_or_none(scenario_payload.get("threshold_value")),
            baseline_price=self._float_or_none(scenario_payload.get("baseline_price")),
            rule_summary=self._build_rule_summary(scenario_payload),
            time_summary=self._build_time_summary(
                time_behavior=alert.time_behavior,
                recurring_start_date=alert.recurring_start_date,
                recurring_end_date=alert.recurring_end_date,
            ),
            available_actions=self._build_available_actions(alert.status),
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )

    def _build_available_actions(self, status_value: str) -> list[str]:
        if status_value == "paused":
            return ["edit", "resume", "delete"]
        return ["edit", "pause", "delete"]

    def _build_rule_summary(self, scenario_payload: dict[str, object]) -> str:
        scenario = str(scenario_payload["scenario"])
        if scenario == "coin_news":
            return "Any new coin news"

        trigger_mode = str(scenario_payload["trigger_mode"])
        threshold_value = float(scenario_payload["threshold_value"])
        if trigger_mode == "percent":
            direction = "up" if scenario == "price_above" else "down"
            return f"Price {direction} {threshold_value:g}% from baseline"

        comparator = "above" if scenario == "price_above" else "below"
        return f"Price {comparator} ${threshold_value:,.2f}"

    def _float_or_none(self, value: object) -> float | None:
        if value is None:
            return None
        return float(value)

    def _build_time_summary(
        self,
        *,
        time_behavior: str,
        recurring_start_date: date | None,
        recurring_end_date: date | None,
    ) -> str:
        if time_behavior == "daily_recurring" and recurring_start_date and recurring_end_date:
            return (
                f"Once per day from {recurring_start_date.isoformat()} "
                f"to {recurring_end_date.isoformat()}"
            )
        return "One-time alert"
