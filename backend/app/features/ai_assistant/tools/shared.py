from __future__ import annotations

from app.features.ai_assistant.actions import PendingActionCapture
from app.features.ai_assistant.schemas import AssistantPendingActionResponse
from app.features.ai_assistant.tools.contracts import (
    AlertClarificationData,
    AlertData,
    AssetClarificationData,
    AssetData,
    PendingProposalData,
    ToolErrorData,
    ToolResult,
)
from app.features.alerts.schemas import AlertResponse
from app.features.alerts.service import AlertService
from app.features.auth.models import User
from app.features.watchlists.schemas import WatchlistAssetResponse, WatchlistAssetSearchResult
from app.features.watchlists.service import WatchlistService


def safe_error(message: str) -> ToolResult[ToolErrorData]:
    return ToolResult(status="error", data=ToolErrorData(message=message))


def capture_proposal(
    capture: PendingActionCapture | None,
    pending_action: AssistantPendingActionResponse,
) -> ToolResult[PendingProposalData]:
    if capture is not None:
        capture.pending_action = pending_action
    return ToolResult(
        status="confirmation_required",
        data=PendingProposalData(
            action_type=pending_action.action_type,
            summary=pending_action.summary,
        ),
    )


async def resolve_search_asset(
    watchlist_service: WatchlistService,
    query: str,
) -> tuple[WatchlistAssetSearchResult | None, ToolResult[AssetClarificationData] | None]:
    matches = await watchlist_service.search_assets(query)
    exact = [
        item
        for item in matches.items
        if query.casefold()
        in {item.asset_id.casefold(), item.symbol.casefold(), item.name.casefold()}
    ]
    if len(exact) == 1:
        return exact[0], None
    return None, asset_clarification(query, matches.items)


async def resolve_saved_asset(
    watchlist_service: WatchlistService,
    user: User,
    query: str,
) -> tuple[WatchlistAssetResponse | None, ToolResult[AssetClarificationData] | None]:
    watchlist = await watchlist_service.get_watchlist(user)
    matches = [
        asset
        for asset in watchlist.assets
        if query.casefold()
        in {asset.asset_id.casefold(), asset.symbol.casefold(), asset.name.casefold()}
    ]
    if len(matches) == 1:
        return matches[0], None
    return None, asset_clarification(query, matches)


def asset_clarification(
    query: str,
    matches: list[WatchlistAssetSearchResult] | list[WatchlistAssetResponse],
) -> ToolResult[AssetClarificationData]:
    return ToolResult(
        status="clarification_needed",
        data=AssetClarificationData(
            message="Please clarify which asset you mean.",
            query=query,
            matches=[AssetData(symbol=asset.symbol, name=asset.name) for asset in matches[:5]],
        ),
    )


async def resolve_alert(
    alert_service: AlertService,
    user: User,
    query: str,
) -> tuple[AlertResponse | None, ToolResult[AlertClarificationData] | None]:
    alerts = await alert_service.list_alerts(user)
    matches = [
        item
        for item in alerts.items
        if query.casefold()
        in {item.symbol.casefold(), item.name.casefold(), item.rule_summary.casefold()}
    ]
    if len(matches) == 1:
        return matches[0], None
    return None, ToolResult(
        status="clarification_needed",
        data=AlertClarificationData(
            message="Please clarify which alert you mean.",
            matches=[
                AlertData(
                    coin=f"{item.name} ({item.symbol})",
                    status=item.status,
                    rule=item.rule_summary,
                    schedule=item.time_summary,
                )
                for item in matches[:5]
            ],
        ),
    )
