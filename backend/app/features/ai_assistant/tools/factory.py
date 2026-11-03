from __future__ import annotations

from langchain_core.tools import BaseTool

from app.features.ai_assistant.actions import AssistantActionService, PendingActionCapture
from app.features.ai_assistant.models import AssistantConversation
from app.features.ai_assistant.tools.alert_tools import build_alert_tools
from app.features.ai_assistant.tools.calculation_tools import build_calculation_tools
from app.features.ai_assistant.tools.chart_tools import build_chart_tools
from app.features.ai_assistant.tools.contracts import ChartPayloadCapture, SourcesCapture
from app.features.ai_assistant.tools.read_tools import build_read_tools as build_base_read_tools
from app.features.ai_assistant.tools.watchlist_tools import build_watchlist_tools
from app.features.alerts.service import AlertService
from app.features.auth.models import User
from app.features.market_data.service import MarketDataService
from app.features.news.service import NewsService
from app.features.watchlists.service import WatchlistService


def build_read_tools(
    *,
    user: User,
    market_data_service: MarketDataService,
    news_service: NewsService,
    watchlist_service: WatchlistService,
    alert_service: AlertService,
    conversation: AssistantConversation | None = None,
    action_service: AssistantActionService | None = None,
    chart_payload_capture: ChartPayloadCapture | None = None,
    pending_action_capture: PendingActionCapture | None = None,
    sources_capture: SourcesCapture | None = None,
) -> list[BaseTool]:
    """Create request-scoped tools; ownership is always derived from ``user``."""
    return [
        *build_base_read_tools(
            user=user,
            market_data_service=market_data_service,
            news_service=news_service,
            watchlist_service=watchlist_service,
            alert_service=alert_service,
            sources_capture=sources_capture,
        ),
        *build_chart_tools(
            market_data_service=market_data_service,
            chart_payload_capture=chart_payload_capture,
            sources_capture=sources_capture,
        ),
        *build_calculation_tools(
            user=user,
            market_data_service=market_data_service,
            alert_service=alert_service,
            sources_capture=sources_capture,
        ),
        *build_watchlist_tools(
            user=user,
            watchlist_service=watchlist_service,
            conversation=conversation,
            action_service=action_service,
            pending_action_capture=pending_action_capture,
        ),
        *build_alert_tools(
            user=user,
            watchlist_service=watchlist_service,
            alert_service=alert_service,
            conversation=conversation,
            action_service=action_service,
            pending_action_capture=pending_action_capture,
        ),
    ]
