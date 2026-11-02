## Summary

Add an automated evaluation suite that sends scripted English conversations to the AI assistant running on a real Groq model and checks which tools the agent selected and with which arguments. Run the suite in CI for pull requests targeting the `dev` branch and fail the run when fewer than 90% of scenarios pass.

## Problem

The assistant's existing unit tests replace the language model with stubs, so they verify graph wiring but not whether the model actually chooses the right tool for a user request. A prompt edit, tool description change, or model switch can silently break tool selection, multi-turn clarification, or the propose-then-confirm boundary, and nothing in CI detects the regression.

## Proposed Solution

Introduce a backend eval suite built on pytest and LangChain `agentevals` trajectory matching:

- each scenario is a declarative case with one or more English user turns and the expected tool-call trajectory;
- the suite runs the real assistant graph and registered tools against a real Groq model (default: the production model `openai/gpt-oss-120b`, overridable through a dedicated eval model setting);
- product services behind the tools are replaced with stubs returning fixed data, because only tool selection and arguments are evaluated, not service responses;
- the suite reports per-scenario results and fails when the pass rate is below 90%;
- a dedicated CI job runs the suite for pull requests targeting `dev` using a `GROQ_API_KEY` repository secret.

## Scope

Affected domain: `ai-assistant-evals` (new). Covered existing assistant workflows:

- coin overview, coin news, and price chart requests;
- listing watchlist assets and alerts;
- proposing watchlist asset additions and removals;
- proposing alert creation, update, pause, resume, and deletion;
- multi-turn flows where the assistant must ask for missing information before proposing a change;
- the confirmation boundary: mutation requests produce only a proposal and never execute a mutation;
- prompt-injection, internal-disclosure, and unsupported-action requests that must not trigger any tool.

## Non-Goals

- evaluating response text quality, tone, or factual correctness;
- LLM-as-judge scoring;
- LangSmith integration in the suite (LangSmith stays a manual monitoring tool);
- scenarios in languages other than English;
- scenarios for behavior introduced by later changes (data sources, deterministic calculations, long-conversation memory, response feedback); those changes add their own scenarios;
- changing assistant behavior, prompts, tools, API contracts, or frontend code;
- running the suite on every pull request or on pushes to `main`;
- automatic retries of failed scenarios.

## Impact

- Backend gains an eval test package, a `make` target, a dev dependency on `agentevals`, and an eval model setting.
- CI gains a job for pull requests targeting `dev` that requires a `GROQ_API_KEY` secret and incurs Groq usage per run.
- No runtime behavior, database, OpenAPI, or Orval changes.
