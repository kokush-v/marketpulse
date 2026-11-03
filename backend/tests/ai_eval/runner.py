from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agentevals.trajectory.match import create_trajectory_match_evaluator
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import Runnable

from app.features.ai_assistant.graph import AssistantGraph
from app.features.ai_assistant.tools import build_read_tools
from tests.ai_eval.scenario_format import MISSING, AnyOf, ExpectedToolCall, Scenario, Turn
from tests.ai_eval.stubs import (
    EvalRecorder,
    StubActionService,
    StubAlertService,
    StubMarketDataService,
    StubNewsService,
    StubWatchlistService,
    stub_conversation,
    stub_user,
)

PASS_RATE_THRESHOLD = 0.9


@dataclass
class TurnResult:
    user: str
    expected: tuple[ExpectedToolCall, ...]
    actual: list[dict[str, Any]] = field(default_factory=list)
    reply: str = ""
    passed: bool = False
    reason: str | None = None


@dataclass
class ScenarioResult:
    scenario: Scenario
    turns: list[TurnResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.turns) == len(self.scenario.turns) and all(
            turn.passed for turn in self.turns
        )


async def run_scenario(
    scenario: Scenario,
    model: Runnable[list[BaseMessage], AIMessage],
) -> ScenarioResult:
    recorder = EvalRecorder()
    watchlist_service = StubWatchlistService(recorder)
    alert_service = StubAlertService(recorder)
    tools = build_read_tools(
        user=stub_user(),
        market_data_service=StubMarketDataService(),  # type: ignore[arg-type]
        news_service=StubNewsService(),  # type: ignore[arg-type]
        watchlist_service=watchlist_service,  # type: ignore[arg-type]
        alert_service=alert_service,  # type: ignore[arg-type]
        conversation=stub_conversation(),
        action_service=StubActionService(recorder),  # type: ignore[arg-type]
    )
    graph = AssistantGraph(model, tools=tools)
    history: list[BaseMessage] = []
    result = ScenarioResult(scenario=scenario)

    for scenario_turn in scenario.turns:
        recorder.reset()
        turn_result = TurnResult(user=scenario_turn.user, expected=scenario_turn.expected)
        result.turns.append(turn_result)
        history = [*history, HumanMessage(content=scenario_turn.user)]
        try:
            state = await graph.compiled.ainvoke({"messages": history, "tool_call_count": 0})
        except Exception as error:
            turn_result.reason = f"model error: {type(error).__name__}"
            break

        turn_messages: list[BaseMessage] = state["messages"][len(history) - 1 :]
        history = list(state["messages"])
        turn_result.actual = [
            {"name": tool_call["name"], "args": tool_call["args"]}
            for message in turn_messages
            if isinstance(message, AIMessage)
            for tool_call in message.tool_calls
        ]
        final_message = turn_messages[-1]
        turn_result.reply = final_message.content if isinstance(final_message.content, str) else ""
        turn_result.passed, turn_result.reason = evaluate_turn(
            scenario, scenario_turn, turn_messages, turn_result.actual, recorder
        )
        if not turn_result.passed:
            break

    return result


def evaluate_turn(
    scenario: Scenario,
    scenario_turn: Turn,
    turn_messages: list[BaseMessage],
    actual: list[dict[str, Any]],
    recorder: EvalRecorder,
) -> tuple[bool, str | None]:
    if recorder.mutations:
        return False, f"mutation executed during agent run: {recorder.mutations}"
    if scenario_turn.expect_no_proposal and recorder.proposals:
        return False, f"expected no proposal, captured: {recorder.proposals}"
    if not scenario_turn.expected:
        if scenario_turn.expect_no_proposal:
            return True, None
        return (not actual), (None if not actual else "expected no tool calls")

    evaluator = create_trajectory_match_evaluator(
        trajectory_match_mode=scenario.trajectory_match_mode,
        tool_args_match_mode=(
            "ignore" if scenario.tool_args_match_mode == "subset" else scenario.tool_args_match_mode
        ),
        tool_args_match_overrides=(
            {call.name: listed_args_matcher(call) for call in scenario_turn.expected}
            if scenario.tool_args_match_mode == "subset"
            else None
        ),
    )
    evaluation = evaluator(
        outputs=turn_messages,
        reference_outputs=reference_trajectory(scenario_turn),
    )
    passed = bool(evaluation["score"])
    return passed, None if passed else "tool calls do not match"


def reference_trajectory(scenario_turn: Turn) -> list[dict[str, Any]]:
    return [
        {"role": "user", "content": scenario_turn.user},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(reference_args(call)),
                    }
                }
                for call in scenario_turn.expected
            ],
        },
    ]


def reference_args(call: ExpectedToolCall) -> dict[str, Any]:
    args = {key: _canonical(value) for key, value in call.args.items()}
    return {key: value for key, value in args.items() if value is not MISSING}


def listed_args_matcher(call: ExpectedToolCall) -> Callable[[dict, dict], bool]:
    """Assert only the listed arguments.

    agentevals ``subset``/``superset`` argument modes are directional, while ``unordered``
    trajectories compare in both directions, so the check accepts the call when both sides
    satisfy the listed expectations.
    """

    def matcher(left: dict, right: dict) -> bool:
        return all(
            _value_matches(side.get(key, MISSING), expected)
            for side in (left, right)
            for key, expected in call.args.items()
        )

    return matcher


def _value_matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, AnyOf):
        return any(_value_matches(actual, option) for option in expected.values)
    if expected is MISSING or actual is MISSING:
        return expected is actual
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return False
        remaining = list(actual)
        for expected_item in expected:
            match = next(
                (item for item in remaining if _value_matches(item, expected_item)),
                MISSING,
            )
            if match is MISSING:
                return False
            remaining.remove(match)
        return True
    if isinstance(expected, str):
        return isinstance(actual, str) and actual.strip().casefold() == expected.casefold()
    if isinstance(expected, int | float) and not isinstance(expected, bool):
        return isinstance(actual, int | float) and float(actual) == float(expected)
    return actual == expected


def _canonical(value: Any) -> Any:
    if isinstance(value, AnyOf):
        return _canonical(value.values[0])
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def pass_rate(results: list[ScenarioResult]) -> float:
    return sum(result.passed for result in results) / len(results) if results else 0.0


def format_report(results: list[ScenarioResult], model_name: str) -> str:
    lines = [f"AI assistant tool evals ({model_name})", ""]
    for result in results:
        lines.append(f"{'PASS' if result.passed else 'FAIL'}  {result.scenario.id}")
        if result.passed:
            continue
        for index, turn_result in enumerate(result.turns, start=1):
            if turn_result.passed:
                continue
            lines.append(f"      turn {index}: {turn_result.user!r}")
            lines.append(f"      reason:   {turn_result.reason}")
            lines.append(f"      expected: {_format_expected(turn_result.expected)}")
            lines.append(f"      actual:   {json.dumps(turn_result.actual)}")
            lines.append(f"      reply:    {turn_result.reply[:200]!r}")
    passed = sum(result.passed for result in results)
    lines += [
        "",
        f"Passed {passed}/{len(results)} scenarios ({pass_rate(results):.0%}); "
        f"threshold {PASS_RATE_THRESHOLD:.0%}",
    ]
    return "\n".join(lines)


def _format_expected(expected: tuple[ExpectedToolCall, ...]) -> str:
    if not expected:
        return "no tool calls or any calls without a proposal"
    return json.dumps([{"name": call.name, "args": reference_args(call)} for call in expected])
