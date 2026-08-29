from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from app.features.ai_assistant.actions import AssistantActionService, PendingActionCapture
from app.features.ai_assistant.models import AssistantConversation
from app.features.ai_assistant.schemas import AssistantPendingActionSummaryResponse
from app.features.ai_assistant.tools.contracts import (
    AssetClarificationData,
    AssetProposalInput,
    PendingProposalData,
    ToolErrorData,
    ToolResult,
)
from app.features.ai_assistant.tools.shared import (
    capture_proposal,
    resolve_saved_asset,
    resolve_search_asset,
    safe_error,
)
from app.features.auth.models import User
from app.features.watchlists.service import WatchlistService


def build_watchlist_tools(
    *,
    user: User,
    watchlist_service: WatchlistService,
    conversation: AssistantConversation | None,
    action_service: AssistantActionService | None,
    pending_action_capture: PendingActionCapture | None,
) -> list[BaseTool]:
    @tool("propose_add_watchlist_asset", args_schema=AssetProposalInput)
    async def propose_add_watchlist_asset(
        query: str,
    ) -> ToolResult[PendingProposalData | AssetClarificationData | ToolErrorData]:
        """Propose adding one unambiguous cryptocurrency to the user's watchlist."""
        if action_service is None or conversation is None:
            return safe_error("Watchlist actions are unavailable right now.")
        asset, clarification = await resolve_search_asset(watchlist_service, query)
        if clarification is not None:
            return clarification
        assert asset is not None
        pending_action = await action_service.propose(
            conversation=conversation,
            user=user,
            action_type="add_watchlist_asset",
            target_id=asset.asset_id,
            validated_input={
                "asset_id": asset.asset_id,
                "symbol": asset.symbol,
                "name": asset.name,
                "image_url": asset.image_url,
            },
            summary=AssistantPendingActionSummaryResponse(
                title=f"Add {asset.name} ({asset.symbol}) to your watchlist",
                details=[f"Asset: {asset.name} ({asset.symbol})"],
            ),
        )
        return capture_proposal(pending_action_capture, pending_action)

    @tool("propose_remove_watchlist_asset", args_schema=AssetProposalInput)
    async def propose_remove_watchlist_asset(
        query: str,
    ) -> ToolResult[PendingProposalData | AssetClarificationData | ToolErrorData]:
        """Propose removing one unambiguous saved asset from the user's watchlist."""
        if action_service is None or conversation is None:
            return safe_error("Watchlist actions are unavailable right now.")
        asset, clarification = await resolve_saved_asset(watchlist_service, user, query)
        if clarification is not None:
            return clarification
        assert asset is not None
        pending_action = await action_service.propose(
            conversation=conversation,
            user=user,
            action_type="remove_watchlist_asset",
            target_id=asset.asset_id,
            validated_input={},
            summary=AssistantPendingActionSummaryResponse(
                title=f"Remove {asset.name} ({asset.symbol}) from your watchlist",
                details=[f"Asset: {asset.name} ({asset.symbol})"],
            ),
        )
        return capture_proposal(pending_action_capture, pending_action)

    return [propose_add_watchlist_asset, propose_remove_watchlist_asset]
