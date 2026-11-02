## Context

The assistant runs as a LangGraph flow (`app/features/ai_assistant/graph.py`) with tools built in `app/features/ai_assistant/tools/`. Mutating tools are `propose_*` tools that only capture a pending proposal; execution happens later through the confirmation path in `actions.py` / `service.py`. Existing unit tests stub the model. Production uses `openai/gpt-oss-120b` on Groq (`GROQ_MODEL`), which supports tool calling but not parallel tool calls.

## Decisions

### Real model, stubbed services

The suite calls the real Groq model through the same model construction used in production (`temperature=0`) and binds the same registered tools. Services, repositories, and providers used by the tools are replaced by in-memory stubs returning fixed, valid data so a scenario outcome depends only on the agent's choices. No database, market-data API, or news provider is required.

### Trajectory matching with agentevals

Scenarios are compared with `agentevals` trajectory match evaluators:

- default trajectory match mode: `unordered` (the same tool calls, in any order); a scenario may declare `strict`, `subset`, or `superset` when the default is not appropriate;
- default tool-argument match mode: `subset` on the arguments listed in the scenario, so only the arguments that matter are asserted;
- per-tool overrides are allowed where normalization makes exact matching meaningless (for example case-insensitive symbols).

A scenario that expects no tool call (clarification, refusal) passes only when the agent makes no tool calls in that turn.

### Scenario format

Scenarios live in the repository under `backend/tests/ai_eval/` as declarative data (one entry per scenario: id, description, ordered user turns, expected tool calls per turn, optional match modes). Adding a scenario does not require new runner code. All scenarios are in English.

### Multi-turn scenarios

Each turn is sent with the accumulated conversation history (user messages, assistant messages, tool messages) produced by earlier turns, mirroring how the service passes history to the graph. Expectations are evaluated per turn; a scenario passes only when every turn passes.

### Confirmation boundary

Mutation scenarios assert that the agent calls the matching `propose_*` tool and that the stubbed mutation services record no executed mutation during the agent run.

### Pass-rate threshold

Each scenario produces a pass/fail result. The suite aggregates results, prints a per-scenario report (id, pass/fail, expected vs actual tool calls for failures), and exits non-zero when the pass rate is below 90%. Individual scenario failures do not fail the run on their own when the threshold is met. The threshold is a single constant in the suite.

Errors calling the model (missing key, provider outage, rate limit after the client's built-in retries) are reported as scenario failures with the error category; a missing `GROQ_API_KEY` fails the run immediately with a clear message instead of reporting 0%.

### Configuration

A new optional setting `ASSISTANT_EVAL_GROQ_MODEL` selects the eval model; when unset the suite uses `GROQ_MODEL`. The suite is invoked through `make test-ai-eval` and lives outside `tests/unit`, so `make test-unit` and the existing CI unit job never call Groq.

### CI

A separate GitHub Actions job runs `make test-ai-eval` only for `pull_request` events whose base branch is `dev`. It reads `GROQ_API_KEY` from repository secrets. Scenarios run sequentially to stay within Groq rate limits.

## Risks

- **Nondeterminism:** even at `temperature=0` the model can vary; the 90% threshold absorbs occasional flakes.
- **Rate limits and cost:** each run makes several model calls per scenario; Groq plan limits may slow or fail runs. Keep the initial scenario set focused (roughly 20–30 scenarios).
- **Fork PRs:** secrets are unavailable to forked pull requests; the job fails with the missing-key message in that case.
- **Model changes:** switching the production model may require scenario adjustments; the eval model setting allows trying a candidate model before switching.

## Rollback

Remove the CI job and the `test-ai-eval` target; no runtime or data changes are involved.
