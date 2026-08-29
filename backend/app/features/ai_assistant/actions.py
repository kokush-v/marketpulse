from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from app.features.ai_assistant.models import AssistantConversation, AssistantPendingAction
from app.features.ai_assistant.repository import AssistantRepository
from app.features.ai_assistant.schemas import (
    AssistantPendingActionResponse,
    AssistantPendingActionSummaryResponse,
)
from app.features.alerts.schemas import CreateAlertRequest, UpdateAlertRequest
from app.features.alerts.service import AlertService
from app.features.auth.models import User
from app.features.watchlists.schemas import AddWatchlistAssetRequest
from app.features.watchlists.service import WatchlistService

PendingActionType = Literal[
    "add_watchlist_asset",
    "remove_watchlist_asset",
    "create_alert",
    "update_alert",
    "pause_alert",
    "resume_alert",
    "delete_alert",
]


@dataclass
class PendingActionCapture:
    pending_action: AssistantPendingActionResponse | None = None


class AssistantActionService:
    def __init__(
        self,
        *,
        repository: AssistantRepository,
        watchlist_service: WatchlistService,
        alert_service: AlertService,
        proposal_ttl_seconds: int = 600,
    ) -> None:
        self.repository = repository
        self.watchlist_service = watchlist_service
        self.alert_service = alert_service
        self.proposal_ttl_seconds = proposal_ttl_seconds

    async def propose(
        self,
        *,
        conversation: AssistantConversation,
        user: User,
        action_type: PendingActionType,
        target_id: str,
        validated_input: dict[str, object],
        summary: AssistantPendingActionSummaryResponse,
    ) -> AssistantPendingActionResponse:
        action = await self.repository.create_pending_action(
            conversation=conversation,
            user_id=user.id,
            action_type=action_type,
            target_id=target_id,
            validated_input=validated_input,
            display_summary=summary.model_dump(mode="json"),
            expires_at=datetime.now(UTC) + timedelta(seconds=self.proposal_ttl_seconds),
        )
        return self.to_response(action)

    async def confirm(
        self,
        *,
        user: User,
        conversation_id: UUID,
        action_id: UUID,
    ) -> tuple[AssistantPendingActionResponse, str]:
        user_id = user.id
        action = await self.repository.claim_pending_action(
            user_id=user_id,
            conversation_id=conversation_id,
            action_id=action_id,
        )
        if action is None:
            raise AssistantActionError("Pending action not found", not_found=True)
        if action.status == "expired":
            raise AssistantActionError("This confirmation has expired")
        if action.status != "executing":
            raise AssistantActionError("This confirmation has already been resolved")

        try:
            result_message = await self._execute(user, action)
        except Exception:
            await self.repository.session.rollback()
            recovered_action = await self.repository.get_pending_action_for_user(
                user_id=user_id,
                conversation_id=conversation_id,
                action_id=action_id,
            )
            if recovered_action is not None and recovered_action.status == "executing":
                recovered_action.status = "pending"
                await self.repository.session.commit()
            raise

        await self.repository.resolve_pending_action(action=action, status="confirmed")
        return self.to_response(action), result_message

    async def cancel(
        self,
        *,
        user: User,
        conversation_id: UUID,
        action_id: UUID,
    ) -> AssistantPendingActionResponse:
        action = await self.repository.cancel_pending_action(
            user_id=user.id,
            conversation_id=conversation_id,
            action_id=action_id,
        )
        if action is None:
            raise AssistantActionError("Pending action not found", not_found=True)
        if action.status == "expired":
            raise AssistantActionError("This confirmation has expired")
        if action.status != "cancelled":
            raise AssistantActionError("This confirmation has already been resolved")
        return self.to_response(action)

    async def _execute(self, user: User, action: AssistantPendingAction) -> str:
        payload = action.validated_input
        if action.action_type == "add_watchlist_asset":
            asset = await self.watchlist_service.add_asset(
                user,
                AddWatchlistAssetRequest.model_validate(payload),
            )
            return f"Added **{asset.name} ({asset.symbol})** to your watchlist."
        if action.action_type == "remove_watchlist_asset":
            await self.watchlist_service.remove_asset(user, action.target_id)
            return f"Removed **{action.display_summary['title']}** from your watchlist."
        if action.action_type == "create_alert":
            alert = await self.alert_service.create_alert(
                user,
                CreateAlertRequest.model_validate(payload),
            )
            return f"Created alert for **{alert.name} ({alert.symbol})**: {alert.rule_summary}."
        if action.action_type == "update_alert":
            alert = await self.alert_service.update_alert(
                user,
                UUID(action.target_id),
                UpdateAlertRequest.model_validate(payload),
            )
            return f"Updated alert for **{alert.name} ({alert.symbol})**: {alert.rule_summary}."
        if action.action_type == "pause_alert":
            alert = await self.alert_service.pause_alert(user, UUID(action.target_id))
            return f"Paused alert for **{alert.name} ({alert.symbol})**."
        if action.action_type == "resume_alert":
            alert = await self.alert_service.resume_alert(user, UUID(action.target_id))
            return f"Resumed alert for **{alert.name} ({alert.symbol})**."
        if action.action_type == "delete_alert":
            await self.alert_service.delete_alert(user, UUID(action.target_id))
            return f"Deleted **{action.display_summary['title']}**."
        raise AssistantActionError("Unsupported pending action")

    @staticmethod
    def to_response(action: AssistantPendingAction) -> AssistantPendingActionResponse:
        return AssistantPendingActionResponse(
            id=action.id,
            action_type=action.action_type,
            status="pending" if action.status == "executing" else action.status,
            summary=AssistantPendingActionSummaryResponse.model_validate(action.display_summary),
        )


class AssistantActionError(Exception):
    def __init__(self, message: str, *, not_found: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.not_found = not_found
