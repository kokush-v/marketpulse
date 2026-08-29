from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from app.core.config import Settings
from app.features.ai_assistant.graph import (
    SYSTEM_PROMPT,
    AssistantGraph,
    AssistantGraphConfigurationError,
    build_groq_model,
)


class StubModel:
    def __init__(self) -> None:
        self.messages: list[BaseMessage] = []

    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        self.messages = messages
        return AIMessage(content="Bitcoin is a cryptocurrency.")


class ToolCallingStubModel:
    def bind_tools(self, _tools: object) -> ToolCallingStubModel:
        return self

    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        if isinstance(messages[-1], ToolMessage):
            return AIMessage(content="The tool result is 4.")
        return AIMessage(
            content="",
            tool_calls=[{"name": "double_value", "args": {"value": 2}, "id": "call-1"}],
        )


class SuggestedRepliesStubModel:
    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        if messages[0].content.startswith("Generate exactly three"):
            return AIMessage(
                content=(
                    '{"suggested_replies": ['
                    '"Show BTC news", '
                    '"What is the current BTC price?", '
                    '"List my watchlist assets"'
                    "]}"
                )
            )
        return AIMessage(content="Bitcoin is a cryptocurrency.")


class InvalidSuggestedRepliesStubModel:
    async def ainvoke(self, _messages: list[BaseMessage]) -> AIMessage:
        return AIMessage(content="Not JSON")


@pytest.mark.asyncio
async def test_graph_adds_system_prompt_and_returns_model_response() -> None:
    model = StubModel()
    graph = AssistantGraph(model)  # type: ignore[arg-type]

    response = await graph.respond([HumanMessage(content="Tell me about Bitcoin")])

    assert response.content == "Bitcoin is a cryptocurrency."
    assert len(model.messages) == 2
    assert model.messages[0].type == "system"
    assert model.messages[1].content == "Tell me about Bitcoin"


@pytest.mark.asyncio
async def test_graph_executes_a_tool_and_returns_the_follow_up_response() -> None:
    @tool
    async def double_value(value: int) -> int:
        """Double a numeric value."""
        return value * 2

    graph = AssistantGraph(ToolCallingStubModel(), tools=[double_value])  # type: ignore[arg-type]

    response = await graph.respond([HumanMessage(content="Double 2")])

    assert response.content == "The tool result is 4."


def test_graph_bounds_context_by_recent_messages_and_character_budget() -> None:
    graph = AssistantGraph(StubModel(), max_context_messages=3, max_context_characters=20)  # type: ignore[arg-type]
    messages = [
        HumanMessage(content="first message"),
        AIMessage(content="second message"),
        HumanMessage(content="third message"),
        AIMessage(content="final"),
    ]

    bounded = graph._bounded_messages(messages)

    assert [message.content for message in bounded] == ["third message", "final"]


@pytest.mark.asyncio
async def test_graph_returns_model_generated_suggested_replies() -> None:
    graph = AssistantGraph(SuggestedRepliesStubModel())  # type: ignore[arg-type]

    response = await graph.respond_with_suggestions([HumanMessage(content="Tell me about Bitcoin")])

    assert response.message.content == "Bitcoin is a cryptocurrency."
    assert response.suggested_replies == [
        "Show BTC news",
        "What is the current BTC price?",
        "List my watchlist assets",
    ]


@pytest.mark.asyncio
async def test_graph_uses_fallback_suggested_replies_when_model_output_is_invalid() -> None:
    graph = AssistantGraph(InvalidSuggestedRepliesStubModel())  # type: ignore[arg-type]

    response = await graph.respond_with_suggestions([HumanMessage(content="Tell me about Bitcoin")])

    assert len(response.suggested_replies) == 3
    assert len(set(response.suggested_replies)) == 3


def test_groq_model_requires_server_side_api_key() -> None:
    config = Settings(groq_api_key=None)

    with pytest.raises(AssistantGraphConfigurationError, match="GROQ_API_KEY"):
        build_groq_model(config)


def test_groq_model_uses_configured_output_token_limit() -> None:
    config = Settings(groq_api_key="test-key", groq_max_tokens=512)

    model = build_groq_model(config)

    assert model.max_tokens == 512


def test_system_prompt_discourages_unnecessary_tables() -> None:
    assert "Markdown lists by default" in SYSTEM_PROMPT
    assert "only when the user asks" in SYSTEM_PROMPT
    assert "single coin summary" in SYSTEM_PROMPT
