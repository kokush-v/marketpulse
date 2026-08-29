from __future__ import annotations

from typing import Literal

from langchain_core.tools import BaseTool, tool

from app.features.ai_assistant.actions import AssistantActionService, PendingActionCapture
from app.features.ai_assistant.models import AssistantConversation
from app.features.ai_assistant.schemas import AssistantPendingActionSummaryResponse
from app.features.ai_assistant.tools.contracts import (
    AlertClarificationData,
    AlertProposalInput,
    AlertTargetInput,
    AssetClarificationData,
    MissingAlertData,
    PendingProposalData,
    ToolErrorData,
    ToolResult,
    UpdateAlertProposalInput,
)
from app.features.ai_assistant.tools.shared import (
    capture_proposal,
    resolve_alert,
    resolve_saved_asset,
    safe_error,
)
from app.features.alerts.service import AlertService
from app.features.auth.models import User
from app.features.watchlists.service import WatchlistService


def build_alert_tools(
    *,
    user: User,
    watchlist_service: WatchlistService,
    alert_service: AlertService,
    conversation: AssistantConversation | None,
    action_service: AssistantActionService | None,
    pending_action_capture: PendingActionCapture | None,
) -> list[BaseTool]:
    @tool("propose_create_alert", args_schema=AlertProposalInput)
    async def propose_create_alert(**kwargs: object) -> AlertProposalResult:
        """Propose a new alert after all required alert details are known."""
        return await propose_alert_upsert(
            action_service=action_service,
            conversation=conversation,
            pending_action_capture=pending_action_capture,
            watchlist_service=watchlist_service,
            user=user,
            payload=AlertProposalInput.model_validate(kwargs),
            action_type="create_alert",
        )

    @tool("propose_update_alert", args_schema=UpdateAlertProposalInput)
    async def propose_update_alert(alert: str, **kwargs: object) -> UpdateAlertProposalResult:
        """Propose updating one owned alert after all required replacement details are known."""
        if action_service is None or conversation is None:
            return safe_error("Alert actions are unavailable right now.")
        target, clarification = await resolve_alert(alert_service, user, alert)
        if clarification is not None:
            return clarification
        assert target is not None
        return await propose_alert_upsert(
            action_service=action_service,
            conversation=conversation,
            pending_action_capture=pending_action_capture,
            watchlist_service=watchlist_service,
            user=user,
            payload=AlertProposalInput.model_validate(kwargs),
            action_type="update_alert",
            target_id=str(target.id),
            target_label=f"{target.name} ({target.symbol})",
        )

    @tool("propose_pause_alert", args_schema=AlertTargetInput)
    async def propose_pause_alert(alert: str) -> AlertLifecycleResult:
        """Propose pausing one unambiguous owned alert."""
        return await propose_alert_lifecycle(
            action_service,
            conversation,
            pending_action_capture,
            alert_service,
            user,
            alert,
            "pause_alert",
        )

    @tool("propose_resume_alert", args_schema=AlertTargetInput)
    async def propose_resume_alert(alert: str) -> AlertLifecycleResult:
        """Propose resuming one unambiguous owned alert."""
        return await propose_alert_lifecycle(
            action_service,
            conversation,
            pending_action_capture,
            alert_service,
            user,
            alert,
            "resume_alert",
        )

    @tool("propose_delete_alert", args_schema=AlertTargetInput)
    async def propose_delete_alert(alert: str) -> AlertLifecycleResult:
        """Propose deleting one unambiguous owned alert."""
        return await propose_alert_lifecycle(
            action_service,
            conversation,
            pending_action_capture,
            alert_service,
            user,
            alert,
            "delete_alert",
        )

    return [
        propose_create_alert,
        propose_update_alert,
        propose_pause_alert,
        propose_resume_alert,
        propose_delete_alert,
    ]


AlertProposalResult = ToolResult[
    PendingProposalData | AssetClarificationData | MissingAlertData | ToolErrorData
]
UpdateAlertProposalResult = ToolResult[
    PendingProposalData
    | AssetClarificationData
    | AlertClarificationData
    | MissingAlertData
    | ToolErrorData
]
AlertLifecycleResult = ToolResult[PendingProposalData | AlertClarificationData | ToolErrorData]


async def propose_alert_upsert(
    *,
    action_service: AssistantActionService | None,
    conversation: AssistantConversation | None,
    pending_action_capture: PendingActionCapture | None,
    watchlist_service: WatchlistService,
    user: User,
    payload: AlertProposalInput,
    action_type: Literal["create_alert", "update_alert"],
    target_id: str | None = None,
    target_label: str | None = None,
) -> AlertProposalResult:
    if action_service is None or conversation is None:
        return safe_error("Alert actions are unavailable right now.")
    missing = missing_alert_fields(payload)
    if missing:
        return ToolResult(
            status="clarification_needed",
            data=MissingAlertData(
                message="Please provide the missing alert details.",
                missing_fields=missing,
            ),
        )
    assert payload.asset is not None and payload.scenario is not None
    asset, clarification = await resolve_saved_asset(watchlist_service, user, payload.asset)
    if clarification is not None:
        return clarification
    assert asset is not None
    pending_action = await action_service.propose(
        conversation=conversation,
        user=user,
        action_type=action_type,
        target_id=target_id or asset.asset_id,
        validated_input={
            "asset_id": asset.asset_id,
            "symbol": asset.symbol,
            "name": asset.name,
            "image_url": asset.image_url,
            "scenario": payload.scenario,
            "time_behavior": payload.time_behavior,
            "recurring_start_date": (
                payload.recurring_start_date.isoformat() if payload.recurring_start_date else None
            ),
            "recurring_end_date": (
                payload.recurring_end_date.isoformat() if payload.recurring_end_date else None
            ),
            "trigger_mode": payload.trigger_mode,
            "threshold_value": payload.threshold_value,
        },
        summary=AssistantPendingActionSummaryResponse(
            title=(
                f"{'Create' if action_type == 'create_alert' else 'Update'} "
                f"alert for {asset.name} ({asset.symbol})"
            ),
            details=[
                f"Rule: {alert_rule_label(payload)}",
                f"Timing: {alert_timing_label(payload)}",
                *([f"Target: {target_label}"] if target_label else []),
            ],
        ),
    )
    return capture_proposal(pending_action_capture, pending_action)


async def propose_alert_lifecycle(
    action_service: AssistantActionService | None,
    conversation: AssistantConversation | None,
    capture: PendingActionCapture | None,
    alert_service: AlertService,
    user: User,
    query: str,
    action_type: Literal["pause_alert", "resume_alert", "delete_alert"],
) -> AlertLifecycleResult:
    if action_service is None or conversation is None:
        return safe_error("Alert actions are unavailable right now.")
    alert, clarification = await resolve_alert(alert_service, user, query)
    if clarification is not None:
        return clarification
    assert alert is not None
    label = {
        "pause_alert": "Pause",
        "resume_alert": "Resume",
        "delete_alert": "Delete",
    }[action_type]
    pending_action = await action_service.propose(
        conversation=conversation,
        user=user,
        action_type=action_type,
        target_id=str(alert.id),
        validated_input={},
        summary=AssistantPendingActionSummaryResponse(
            title=f"{label} alert for {alert.name} ({alert.symbol})",
            details=[f"Rule: {alert.rule_summary}", f"Status: {alert.status}"],
        ),
    )
    return capture_proposal(capture, pending_action)


def missing_alert_fields(payload: AlertProposalInput) -> list[str]:
    missing = [field for field in ("asset", "scenario") if getattr(payload, field) is None]
    if payload.scenario in {"price_above", "price_below"}:
        if payload.trigger_mode is None:
            missing.append("trigger_mode")
        if payload.threshold_value is None:
            missing.append("threshold_value")
    if payload.time_behavior == "daily_recurring":
        if payload.recurring_start_date is None:
            missing.append("recurring_start_date")
        if payload.recurring_end_date is None:
            missing.append("recurring_end_date")
    return missing


def alert_rule_label(payload: AlertProposalInput) -> str:
    if payload.scenario == "coin_news":
        return "Any new coin news"
    direction = "above" if payload.scenario == "price_above" else "below"
    suffix = "%" if payload.trigger_mode == "percent" else "USD"
    return f"Price {direction} {payload.threshold_value:g} {suffix}"


def alert_timing_label(payload: AlertProposalInput) -> str:
    if payload.time_behavior == "daily_recurring":
        return f"Daily from {payload.recurring_start_date} to {payload.recurring_end_date}"
    return "One-time"
