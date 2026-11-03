from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.features.ai_assistant.graph import AssistantGraph, AssistantGraphResponse
from app.features.ai_assistant.schemas import (
    AssistantConversationResponse,
    SendAssistantMessageRequest,
)
from app.features.ai_assistant.service import AssistantService, AssistantServiceError
from app.features.auth.models import User

NOW = datetime.now(UTC)


class SummaryModel:
    def __init__(
        self, summary: str = "Coins: SOL price was asked; it was about $180 then."
    ) -> None:
        self.summary = summary
        self.calls: list[list[BaseMessage]] = []

    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        self.calls.append(messages)
        return AIMessage(content=self.summary)


class FailingSummaryModel:
    async def ainvoke(self, _messages: list[BaseMessage]) -> AIMessage:
        raise RuntimeError("summarization failed")


class RecordingModel:
    def __init__(self) -> None:
        self.messages: list[BaseMessage] = []

    def bind_tools(self, _tools: object) -> RecordingModel:
        return self

    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        self.messages = messages
        return AIMessage(content="Answer")


def _messages(count: int, *, start: int = 0) -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            id=uuid4(),
            sequence=sequence,
            role="user" if sequence % 2 == 0 else "assistant",
            content=f"message {sequence}",
            created_at=NOW,
        )
        for sequence in range(start, start + count)
    ]


def _conversation(
    *, summary: str | None = None, summarized_through: int | None = None
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        title="Chat",
        created_at=NOW,
        updated_at=NOW,
        context_summary=summary,
        summarized_through_sequence=summarized_through,
    )


def _service(model: object, messages: list[SimpleNamespace], conversation: Any) -> AssistantService:
    service = AssistantService(
        session=cast(Any, None),
        market_data_service=cast(Any, None),
        news_service=cast(Any, None),
        watchlist_service=cast(Any, None),
        alert_service=cast(Any, None),
    )
    service._model = model
    service.repository = cast(
        Any,
        SimpleNamespace(
            get_conversation_for_user=AsyncMock(return_value=conversation),
            get_current_pending_action_for_user=AsyncMock(return_value=None),
            list_messages_for_conversation=AsyncMock(return_value=messages),
            record_compaction=AsyncMock(),
            append_message=AsyncMock(),
        ),
    )
    service._get_graph_response = AsyncMock(  # type: ignore[method-assign]
        return_value=AssistantGraphResponse(
            message=AIMessage(content="Reply"), suggested_replies=[]
        )
    )
    return service


async def _send(service: AssistantService, conversation: Any) -> None:
    await service.send_message(
        cast(User, SimpleNamespace(id=uuid4())),
        conversation.id,
        SendAssistantMessageRequest(content="Show me the latest news for it"),
    )


@pytest.mark.asyncio
async def test_no_compaction_while_the_conversation_fits_the_window() -> None:
    model = SummaryModel()
    conversation = _conversation()
    service = _service(model, _messages(9), conversation)

    await _send(service, conversation)

    assert model.calls == []
    service.repository.record_compaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_compaction_summarizes_messages_that_left_the_window() -> None:
    model = SummaryModel()
    conversation = _conversation()
    # 12 stored messages plus the new one: the 10-message window keeps 9 stored messages.
    service = _service(model, _messages(12), conversation)

    await _send(service, conversation)

    prompt = model.calls[0][-1].content
    assert "Previous summary:\nNone" in prompt
    assert all(f"message {sequence}" in prompt for sequence in (0, 1, 2))
    assert "message 3" not in prompt
    service.repository.record_compaction.assert_awaited_once_with(
        conversation=conversation,
        summary=model.summary,
        summarized_through_sequence=2,
        marker_content="Context compacted",
    )
    first_appended = service.repository.append_message.await_args_list[0].kwargs
    assert first_appended["role"] == "user"


@pytest.mark.asyncio
async def test_compaction_only_summarizes_newly_out_of_window_messages() -> None:
    model = SummaryModel(summary="Updated summary")
    conversation = _conversation(summary="Earlier summary", summarized_through=2)
    marker = SimpleNamespace(
        id=uuid4(), sequence=3, role="compaction", content="Context compacted", created_at=NOW
    )
    messages = [*_messages(3), marker, *_messages(10, start=4)]
    service = _service(model, messages, conversation)

    await _send(service, conversation)

    prompt = model.calls[0][-1].content
    assert "Previous summary:\nEarlier summary" in prompt
    assert "message 4" in prompt
    assert "message 2" not in prompt
    assert "Context compacted" not in prompt
    assert (
        service.repository.record_compaction.await_args.kwargs["summarized_through_sequence"] == 4
    )


@pytest.mark.asyncio
async def test_already_summarized_messages_are_not_compacted_again() -> None:
    model = SummaryModel()
    conversation = _conversation(summary="Earlier summary", summarized_through=2)
    service = _service(model, _messages(12), conversation)

    await _send(service, conversation)

    assert model.calls == []
    service.repository.record_compaction.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("model", [FailingSummaryModel(), SummaryModel(summary="  ")])
async def test_summarization_failure_still_answers_and_adds_no_marker(model: object) -> None:
    conversation = _conversation()
    service = _service(model, _messages(12), conversation)

    await _send(service, conversation)

    service.repository.record_compaction.assert_not_awaited()
    service._get_graph_response.assert_awaited_once()
    roles = [call.kwargs["role"] for call in service.repository.append_message.await_args_list]
    assert roles == ["user", "assistant"]


@pytest.mark.asyncio
async def test_model_context_has_summary_and_open_proposal_but_no_markers() -> None:
    conversation = _conversation(summary="Coins: SOL was discussed.", summarized_through=2)
    service = _service(SummaryModel(), [], conversation)
    service.repository.get_current_pending_action_for_user = AsyncMock(
        return_value=SimpleNamespace(
            action_type="delete_alert",
            display_summary={
                "title": "Delete alert for Bitcoin (BTC)",
                "details": ["Rule: Price above $120,000"],
            },
            expires_at=NOW + timedelta(minutes=10),
        )
    )
    context = await service._conversation_context_messages(
        cast(User, SimpleNamespace(id=uuid4())), cast(Any, conversation)
    )
    history = service._model_history(
        cast(
            Any,
            [
                SimpleNamespace(role="user", content="Tell me about SOL"),
                SimpleNamespace(role="compaction", content="Context compacted"),
                SimpleNamespace(role="assistant", content="SOL is a coin."),
            ],
        )
    )
    model = RecordingModel()
    graph = AssistantGraph(cast(Any, model), context_messages=context)

    await graph.respond([*history, HumanMessage(content="What is waiting for confirmation?")])

    contents = [message.content for message in model.messages]
    assert isinstance(model.messages[1], SystemMessage)
    assert "Coins: SOL was discussed." in contents[1]
    assert "historical" in contents[1]
    assert "Delete alert for Bitcoin (BTC)" in contents[2]
    assert "Rule: Price above $120,000" in contents[2]
    assert contents[3:] == [
        "Tell me about SOL",
        "SOL is a coin.",
        "What is waiting for confirmation?",
    ]
    assert "Context compacted" not in contents


@pytest.mark.asyncio
async def test_expired_proposal_is_not_presented_to_the_model() -> None:
    conversation = _conversation()
    service = _service(SummaryModel(), [], conversation)
    service.repository.get_current_pending_action_for_user = AsyncMock(
        return_value=SimpleNamespace(
            action_type="delete_alert",
            display_summary={"title": "Delete alert", "details": ["Rule: x"]},
            expires_at=NOW - timedelta(seconds=1),
        )
    )

    context = await service._conversation_context_messages(
        cast(User, SimpleNamespace(id=uuid4())), cast(Any, conversation)
    )

    assert context == []


@pytest.mark.asyncio
async def test_compaction_markers_are_returned_only_in_the_owners_conversation() -> None:
    conversation = _conversation(summary="Summary", summarized_through=2)
    marker = SimpleNamespace(
        id=uuid4(),
        sequence=3,
        role="compaction",
        content="Context compacted",
        suggested_replies=[],
        chart_payload=None,
        pending_action=None,
        sources=None,
        feedback=None,
        created_at=NOW,
    )
    service = _service(SummaryModel(), [marker], conversation)
    owner = cast(User, SimpleNamespace(id=uuid4()))

    response = await service.get_conversation(owner, conversation.id)

    assert isinstance(response, AssistantConversationResponse)
    assert [(message.role, message.content) for message in response.messages] == [
        ("compaction", "Context compacted")
    ]
    assert "context_summary" not in response.model_dump()
    service.repository.get_conversation_for_user.assert_awaited_once_with(
        user_id=owner.id, conversation_id=conversation.id
    )

    service.repository.get_conversation_for_user = AsyncMock(return_value=None)
    with pytest.raises(AssistantServiceError) as caught:
        await service.get_conversation(cast(User, SimpleNamespace(id=uuid4())), conversation.id)
    assert caught.value.status_code == 404
