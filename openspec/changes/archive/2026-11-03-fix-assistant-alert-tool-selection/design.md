## Context

Alert proposal tools live in `app/features/ai_assistant/tools/alert_tools.py`; their argument schemas in `tools/contracts.py`; alert lookup in `tools/shared.py` (`resolve_alert`). `resolve_alert` matches the `alert` argument only when it equals an alert's symbol, name, or rule summary exactly (case-insensitive). `AlertTargetInput.alert` is described as a description that "unambiguously identifies" an alert "such as its coin and condition", which leads the model to ask the user instead of calling the tool. `AlertProposalInput.trigger_mode` is optional in the schema but required for price scenarios by `missing_alert_fields`, so the model omits it and the tool returns a clarification.

## Decisions

### Threshold type

The `trigger_mode` description states the mapping: `$`, `USD`, "dollars" mean `currency`; `%`, "percent" mean `percent`; a threshold without a unit is ambiguous and the assistant asks before proposing. The system prompt repeats the rule. The tool keeps rejecting a price alert without `trigger_mode`; no unit is inferred in code.

### Alert identification

`AlertTargetInput.alert` (and `UpdateAlertProposalInput.alert`) is described as the coin name or symbol of the alert, optionally followed by its condition. Matching in `resolve_alert`:

1. Select the user's alerts whose coin matches the argument (symbol, name, or asset ID appearing as a word in the argument, case-insensitive).
2. If several remain and the argument also contains text matching one alert's rule summary, use that alert.
3. Exactly one candidate: use it. Several: return `clarification_needed` listing those alerts (coin, rule, schedule, status). None: return `clarification_needed` with a "no matching alert" message and the user's alerts (up to 5) so the model can offer real options.

Ownership is unchanged: matching runs only over `alert_service.list_alerts(user)`.

The system prompt states: to act on an existing alert, call the matching proposal tool with the coin the user named; never ask the user to describe an alert that a tool can identify; never mention alerts that a tool did not return.

### Timing default

The `time_behavior` description and the system prompt state that an alert is one-time unless the user asks for daily repetition, and that the assistant does not ask about timing otherwise. Daily recurring alerts still require start and end dates.

### Eval scenarios

Stub data adds a second alert for one coin. New scenarios:

- threshold without a unit: no tool call (clarification);
- two alerts for one coin, "pause my <coin> alert": no proposal is captured (the agent may look up alerts or call the pause tool, which returns a clarification);
- two alerts, follow-up naming the condition: pause proposal;
- news alert without timing: create proposal with `scenario=coin_news` (timing not asserted).

The scenario format gains an optional per-turn flag `expect_no_proposal`. When set, the turn fails if the stub action service captured a proposal, and a turn with no expected tool calls accepts any tool calls instead of requiring none. Without the flag, existing scenarios and matching behave as before.

## Risks

- Looser matching could pick an alert the user did not mean when the argument names a coin and a different condition; step 2 and the confirmation step mitigate this.
- Prompt changes can shift other behavior; the full eval suite and unit tests cover regressions.
- Model nondeterminism: the 90% threshold remains the acceptance bar.

## Rollback

Revert the prompt, descriptions, and `resolve_alert` changes; remove the new scenarios.
