from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

AssistantMessageRole = Literal["user", "assistant", "compaction"]
AssistantChartPeriod = Literal["24h", "7d", "30d", "1y"]
AssistantPendingActionType = Literal[
    "add_watchlist_asset",
    "remove_watchlist_asset",
    "create_alert",
    "update_alert",
    "pause_alert",
    "resume_alert",
    "delete_alert",
]
AssistantPendingActionStatus = Literal["pending", "confirmed", "cancelled", "expired"]
AssistantMessageSourceKind = Literal["news", "marketpulse"]
AssistantFeedbackRating = Literal["positive", "negative"]
AssistantErrorCode = Literal[
    "assistant_not_configured",
    "assistant_configuration_error",
    "assistant_rate_limited",
    "assistant_timeout",
    "assistant_unavailable",
    "invalid_model_response",
    "conversation_not_found",
    "invalid_message",
    "invalid_conversation_title",
    "pending_action_not_found",
    "pending_action_resolved",
    "message_not_found",
    "invalid_feedback_target",
    "feedback_already_submitted",
]


class CreateAssistantConversationRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class SendAssistantMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class UpdateAssistantConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class AssistantChartPointResponse(BaseModel):
    time: str = Field(min_length=1)
    price: float


class AssistantChartSeriesResponse(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    points: list[AssistantChartPointResponse] = Field(min_length=1)


class AssistantChartPayloadResponse(BaseModel):
    period: AssistantChartPeriod
    series: list[AssistantChartSeriesResponse] = Field(min_length=1, max_length=5)


class AssistantPendingActionSummaryResponse(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    details: list[str] = Field(min_length=1, max_length=8)


class AssistantPendingActionResponse(BaseModel):
    id: UUID
    action_type: AssistantPendingActionType
    status: AssistantPendingActionStatus
    summary: AssistantPendingActionSummaryResponse


class AssistantMessageSourceResponse(BaseModel):
    kind: AssistantMessageSourceKind
    label: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    url: str | None = None
    updated_at: str | None = None
    stale: bool = False


class SubmitAssistantMessageFeedbackRequest(BaseModel):
    rating: AssistantFeedbackRating
    reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional free-text reason; trimmed, and stored as null when empty.",
    )

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, reason: object) -> object:
        if isinstance(reason, str):
            return reason.strip() or None
        return reason


class AssistantMessageFeedbackResponse(BaseModel):
    rating: AssistantFeedbackRating
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssistantMessageResponse(BaseModel):
    id: UUID
    role: AssistantMessageRole
    content: str
    suggested_replies: list[str] = Field(default_factory=list)
    chart_payload: AssistantChartPayloadResponse | None = None
    pending_action: AssistantPendingActionResponse | None = None
    sources: list[AssistantMessageSourceResponse] = Field(default_factory=list)
    feedback: AssistantMessageFeedbackResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("sources", mode="before")
    @classmethod
    def default_missing_sources(cls, sources: object) -> object:
        return [] if sources is None else sources


class AssistantConversationSummaryResponse(BaseModel):
    id: UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssistantConversationResponse(AssistantConversationSummaryResponse):
    messages: list[AssistantMessageResponse]


class AssistantConversationListResponse(BaseModel):
    items: list[AssistantConversationSummaryResponse]


class AssistantErrorResponse(BaseModel):
    code: AssistantErrorCode
    message: str
    retryable: bool = False
    retry_after_seconds: int | None = Field(default=None, ge=1)
