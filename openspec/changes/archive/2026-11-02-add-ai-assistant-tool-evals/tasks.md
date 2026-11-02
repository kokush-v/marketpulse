## 1. Setup

- [x] 1.1 Add `agentevals` as a backend dev dependency and update the lock file.
- [x] 1.2 Add the optional `ASSISTANT_EVAL_GROQ_MODEL` setting (fallback to `GROQ_MODEL`) and document it in `backend/.env.example`.
- [x] 1.3 Add a `make test-ai-eval` target that runs only the eval suite, kept outside `tests/unit`.

## 2. Eval Harness

- [x] 2.1 Build in-memory stubs for the services used by assistant tools that return fixed valid data and record attempted mutations.
- [x] 2.2 Build a runner that constructs the real assistant graph with the real Groq model and registered tools over the stubs, sends scenario turns with accumulated history, and captures tool calls per turn.
- [x] 2.3 Define the declarative scenario format (id, description, user turns, expected tool calls per turn, optional trajectory and argument match modes).
- [x] 2.4 Evaluate each turn with `agentevals` trajectory matching (argument `subset` matching by default) and treat "no expected tool calls" as requiring zero tool calls.
- [x] 2.5 Aggregate results, print a per-scenario report with expected vs actual calls for failures, and exit non-zero below a 90% pass rate.
- [x] 2.6 Fail immediately with a clear message when `GROQ_API_KEY` is missing; report model call errors as scenario failures.

## 3. Scenarios (English)

- [x] 3.1 Read scenarios: coin overview, coin news, price chart (single coin, comparison, default period), list watchlist assets, list alerts.
- [x] 3.2 Watchlist scenarios: propose add asset, propose remove asset.
- [x] 3.3 Alert scenarios: propose create, update, pause, resume, and delete.
- [x] 3.4 Multi-turn scenarios: incomplete alert request triggers a clarification with no tool call, and the follow-up turn proposes the alert.
- [x] 3.5 Confirmation boundary: mutation scenarios assert no stubbed mutation is executed during the agent run.
- [x] 3.6 Safety scenarios: prompt-injection, internal-disclosure, unsupported-action, and capability questions trigger no tool call.

## 4. CI

- [x] 4.1 Add a GitHub Actions job that runs `make test-ai-eval` only for pull requests targeting `dev`, using the `GROQ_API_KEY` repository secret.
- [x] 4.2 Document the required repository secret and how to run the suite locally through the backend container.

## 5. Validation

- [x] 5.1 Run the suite locally: `docker compose exec -T backend make test-ai-eval`.
- [x] 5.2 Confirm `make test-unit` does not execute eval scenarios.
- [x] 5.3 Run `docker compose exec -T backend uv run ruff check .` and `docker compose exec -T backend uv run ruff format --check .`.
- [x] 5.4 Run `openspec validate add-ai-assistant-tool-evals --strict`.
