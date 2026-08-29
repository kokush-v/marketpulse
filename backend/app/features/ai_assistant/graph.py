from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field, field_validator

from app.core.config import Settings, settings
from app.features.ai_assistant.schemas import AssistantChartPayloadResponse

SYSTEM_PROMPT = """You are the MarketPulse AI assistant.
Help authenticated users understand cryptocurrency information and use MarketPulse.
Do not provide investment advice or execute trades.
Do not claim an action completed without a tool result.
Ask a concise follow-up question whenever an action request is missing required information.
Use concise prose and Markdown lists by default. Use a Markdown table only when the user asks
for one or when comparing multiple same-shaped records is materially clearer. Do not use a table
for a single coin summary, news explanation, or ordinary response merely because tool data is
structured.
When you use get_price_chart_data, give a concise factual description of the displayed movement
or comparison. Do not give investment advice.
"""

SUGGESTED_REPLIES_PROMPT = """Generate exactly three short suggested next messages for a
MarketPulse user. They must be distinct, directly relevant to the assistant response and
conversation, and suitable to send unchanged as the next user message. Do not offer trading
advice. Return only JSON in this shape: {"suggested_replies": ["...", "...", "..."]}."""

FALLBACK_SUGGESTED_REPLIES = [
    "Tell me more about this.",
    "Show the latest related news.",
    "What should I check next?",
]


class AssistantGraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    tool_call_count: int


class AssistantGraphConfigurationError(RuntimeError):
    """Raised when the server-side assistant model is not configured."""


class SuggestedReplies(BaseModel):
    suggested_replies: list[str] = Field(min_length=3, max_length=3)

    @field_validator("suggested_replies")
    @classmethod
    def validate_replies(cls, replies: list[str]) -> list[str]:
        normalized = [reply.strip() for reply in replies]
        if any(not reply for reply in normalized):
            raise ValueError("Suggested replies must not be blank")
        if len({reply.casefold() for reply in normalized}) != 3:
            raise ValueError("Suggested replies must be distinct")
        return normalized


@dataclass(frozen=True)
class AssistantGraphResponse:
    message: AIMessage
    suggested_replies: list[str]
    chart_payload: AssistantChartPayloadResponse | None = None


def build_groq_model(config: Settings = settings) -> ChatGroq:
    if not config.groq_api_key:
        raise AssistantGraphConfigurationError("GROQ_API_KEY is not configured")

    return ChatGroq(
        model=config.groq_model,
        api_key=config.groq_api_key,
        temperature=0,
        timeout=config.groq_timeout_seconds,
        max_retries=config.groq_max_retries,
        max_tokens=config.groq_max_tokens,
    )


class AssistantGraph:
    """Bounded LangGraph conversation loop with backend-owned domain tools."""

    def __init__(
        self,
        model: Runnable[list[BaseMessage], AIMessage],
        tools: list[BaseTool] | None = None,
        chart_payload_getter: Callable[[], AssistantChartPayloadResponse | None] | None = None,
        max_tool_calls: int = settings.assistant_max_tool_calls,
        max_context_messages: int = settings.assistant_max_context_messages,
        max_context_characters: int = settings.assistant_max_context_characters,
    ) -> None:
        self.tools = tools or []
        self.max_tool_calls = max_tool_calls
        self.max_context_messages = max_context_messages
        self.max_context_characters = max_context_characters
        self.chart_payload_getter = chart_payload_getter
        self.suggestion_model = model
        self.model = model.bind_tools(self.tools) if self.tools else model
        self.tool_node = ToolNode(self.tools) if self.tools else None
        workflow = StateGraph(AssistantGraphState)
        workflow.add_node("assistant", self._call_model)
        workflow.add_edge(START, "assistant")
        if self.tool_node is None:
            workflow.add_edge("assistant", END)
        else:
            workflow.add_node("tools", self._execute_tools)
            workflow.add_conditional_edges("assistant", self._route_after_assistant, ["tools", END])
            workflow.add_edge("tools", "assistant")
        self.compiled = workflow.compile()

    async def _call_model(self, state: AssistantGraphState) -> dict[str, list[AIMessage]]:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *self._bounded_messages(state["messages"]),
        ]
        response = await self.model.ainvoke(messages)
        return {"messages": [response]}

    def _route_after_assistant(self, state: AssistantGraphState) -> str:
        response = state["messages"][-1]
        if not isinstance(response, AIMessage) or not response.tool_calls:
            return END
        if state.get("tool_call_count", 0) >= self.max_tool_calls:
            return END
        return "tools"

    async def _execute_tools(self, state: AssistantGraphState) -> dict[str, object]:
        if self.tool_node is None:
            return {}
        response = state["messages"][-1]
        tool_call_count = len(response.tool_calls) if isinstance(response, AIMessage) else 0
        result = await self.tool_node.ainvoke(state)
        return {
            "messages": result["messages"],
            "tool_call_count": state.get("tool_call_count", 0) + tool_call_count,
        }

    async def respond(self, messages: list[BaseMessage]) -> AIMessage:
        result = await self.compiled.ainvoke({"messages": messages, "tool_call_count": 0})
        response = result["messages"][-1]
        if not isinstance(response, AIMessage):
            raise RuntimeError("Assistant graph did not return an AI response")
        return response

    async def respond_with_suggestions(
        self,
        messages: list[BaseMessage],
    ) -> AssistantGraphResponse:
        response = await self.respond(messages)
        suggested_replies = await self._generate_suggested_replies(messages, response)
        return AssistantGraphResponse(
            message=response,
            suggested_replies=suggested_replies,
            chart_payload=self.chart_payload_getter() if self.chart_payload_getter else None,
        )

    async def _generate_suggested_replies(
        self,
        messages: list[BaseMessage],
        response: AIMessage,
    ) -> list[str]:
        context = [
            SystemMessage(content=SUGGESTED_REPLIES_PROMPT),
            *messages[-4:],
            AIMessage(content=self._message_content(response)),
        ]
        try:
            suggestion_response = await self.suggestion_model.ainvoke(context)
            suggestions = SuggestedReplies.model_validate_json(
                self._message_content(suggestion_response)
            )
            return suggestions.suggested_replies
        except Exception:
            return FALLBACK_SUGGESTED_REPLIES.copy()

    @staticmethod
    def _message_content(message: AIMessage) -> str:
        if isinstance(message.content, str):
            return message.content
        return "\n".join(
            item["text"]
            for item in message.content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        )

    def _bounded_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        recent_messages = messages[-self.max_context_messages :]
        selected: list[BaseMessage] = []
        remaining_characters = self.max_context_characters

        for message in reversed(recent_messages):
            if isinstance(message, AIMessage):
                content = self._message_content(message)
            else:
                content = message.content
            content_size = len(content) if isinstance(content, str) else len(str(content))
            if selected and content_size > remaining_characters:
                break
            selected.append(message)
            remaining_characters -= content_size
            if remaining_characters <= 0:
                break

        return list(reversed(selected))
