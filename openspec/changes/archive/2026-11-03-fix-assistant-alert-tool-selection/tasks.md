## 1. Alert Tool Behavior

- [x] 1.1 Update the `trigger_mode` description: `$`, `USD`, "dollars" mean a fixed USD price; `%`, "percent" mean a percentage change; a threshold without a unit requires asking the user.
- [x] 1.2 Update the `time_behavior` description: one-time unless the user asks for daily repetition; do not ask about timing otherwise.
- [x] 1.3 Update the `alert` argument descriptions for update, pause, resume, and delete: the coin name or symbol of the alert, optionally with its condition.
- [x] 1.4 Change `resolve_alert` to match the user's alerts by coin, narrow by rule summary when several match, return a clarification listing the matching alerts when still ambiguous, and return a "no matching alert" clarification with the user's alerts when none match.
- [x] 1.5 Add system prompt rules for threshold units, the one-time default, identifying alerts through the tools, and never mentioning alerts a tool did not return.

## 2. Backend Tests

- [x] 2.1 Unit tests for `resolve_alert`: single match by coin name and by symbol, several matches narrowed by condition, several matches without a condition (clarification with matches), no match (clarification), and matching limited to the user's own alerts.
- [x] 2.2 Unit tests for alert proposal tools: pause, resume, delete, and update with a coin-only argument produce a proposal when one alert matches.
- [x] 2.3 Run `docker compose exec -T backend make test-unit`.

## 3. Evals

- [x] 3.1 Add an optional per-turn `expect_no_proposal` flag to the scenario format and runner: fail the turn when a proposal was captured; with no expected tool calls, accept any tool calls.
- [x] 3.2 Add a second Solana alert with a different condition to the eval stub data.
- [x] 3.3 Add scenarios: threshold without a unit (no tool call), news alert without timing (create proposal for `coin_news`), several Solana alerts (no proposal, then a pause proposal after the user names the condition).
- [x] 3.4 Run `docker compose exec -T backend make test-ai-eval` and confirm a pass rate of at least 90%.

## 4. Validation

- [x] 4.1 Run `docker compose exec -T backend make lint`.
- [x] 4.2 Run `openspec validate fix-assistant-alert-tool-selection --strict`.
