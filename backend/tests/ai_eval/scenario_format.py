from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TrajectoryMatchMode = Literal["strict", "unordered", "subset", "superset"]
ToolArgsMatchMode = Literal["exact", "ignore", "subset", "superset"]


class _Missing:
    def __repr__(self) -> str:
        return "<missing>"


MISSING = _Missing()
"""Accepted value for an argument the agent may omit (for example a defaulted argument)."""


@dataclass(frozen=True)
class AnyOf:
    """Any of these values is accepted for one argument; the first one is used in reports."""

    values: tuple[Any, ...]

    def __init__(self, *values: Any) -> None:
        object.__setattr__(self, "values", values)


@dataclass(frozen=True)
class ExpectedToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    """Only the listed arguments are asserted. Strings compare case-insensitively."""


@dataclass(frozen=True)
class Turn:
    user: str
    expected: tuple[ExpectedToolCall, ...] = ()
    """Empty means no tool calls are allowed in this turn, unless expect_no_proposal is set."""
    expect_no_proposal: bool = False
    """Fail the turn when a proposal was captured; with no expected calls, accept any tool calls."""


@dataclass(frozen=True)
class Scenario:
    id: str
    description: str
    turns: tuple[Turn, ...]
    trajectory_match_mode: TrajectoryMatchMode = "unordered"
    tool_args_match_mode: ToolArgsMatchMode = "subset"
