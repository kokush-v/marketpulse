"""Tool-selection evals against the real Groq model. Run with `make test-ai-eval`."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.features.ai_assistant.graph import build_groq_model
from tests.ai_eval.runner import PASS_RATE_THRESHOLD, format_report, pass_rate, run_scenario
from tests.ai_eval.scenarios import SCENARIOS


async def test_assistant_tool_selection_meets_pass_rate() -> None:
    if not settings.groq_api_key:
        pytest.fail(
            "GROQ_API_KEY is not configured; the AI assistant eval suite needs a Groq API key.",
            pytrace=False,
        )

    eval_settings = settings.model_copy(
        update={"groq_model": settings.assistant_eval_groq_model or settings.groq_model}
    )
    model = build_groq_model(eval_settings)

    # Sequential on purpose: keeps the run within Groq rate limits.
    results = [await run_scenario(scenario, model) for scenario in SCENARIOS]

    print(format_report(results, eval_settings.groq_model))
    assert pass_rate(results) >= PASS_RATE_THRESHOLD, (
        f"Pass rate {pass_rate(results):.0%} is below {PASS_RATE_THRESHOLD:.0%}"
    )
