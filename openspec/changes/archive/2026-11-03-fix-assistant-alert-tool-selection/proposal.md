## Summary

Fix three assistant alert-handling problems found by the AI assistant eval suite: the assistant asks whether a USD threshold is a price or a percentage even when the user named the unit, asks the user to describe an alert instead of identifying it from the user's alerts, and asks whether an alert should repeat daily even though one-time is the default. Add eval scenarios that cover these cases.

## Problem

The eval suite added by `add-ai-assistant-tool-evals` passes 18–19 of 25 scenarios (72–76%) on the production model, below the 90% threshold, so the eval check fails on every pull request to `dev`. The failures are real user-facing problems:

- "Create an alert when Bitcoin rises above 110000 USD" produces a question "currency or percent?" because the threshold type is not passed to the alert proposal and the proposal is rejected as incomplete.
- "Pause my Bitcoin alert" (and update, resume, delete) produces a request to describe the alert, sometimes with invented example alerts, although the user has exactly one Bitcoin alert. The assistant does not look at the user's alerts and the alert argument requires a description that matches the stored rule exactly.
- "Alert me about any new Solana news" produces a question "once or daily?" although alerts are one-time unless the user asks otherwise.

## Proposed Solution

- Threshold type: a threshold stated with `$`, `USD`, or "dollars" is a fixed USD price; a threshold stated with `%` or "percent" is a percentage change. A threshold without a unit is ambiguous: the assistant asks which one the user means and creates no proposal.
- Alert identification for update, pause, resume, and delete: the user may identify an alert by its coin, optionally with its condition. When exactly one of the user's alerts matches, the assistant proposes the action directly. When several match, the assistant lists the matching alerts (coin, condition, timing, status) and asks which one; it creates no proposal. When none match, the assistant says that no matching alert exists. The assistant never invents alerts.
- Timing: when the user does not mention timing, the alert is one-time; the assistant does not ask about it. The proposal summary continues to show the timing so the user can correct it before confirming.
- Implement through the system prompt, tool argument descriptions, and alert matching in the alert tools.
- Add eval scenarios for each case and require the suite to meet its 90% threshold.

## Scope

Affected domains: `ai-agent-tools` (alert proposals), `ai-assistant-evals` (scenarios).

Primary workflows:

- creating price and news alerts through the assistant;
- updating, pausing, resuming, and deleting an alert through the assistant;
- running the eval suite.

## Non-Goals

- changing alert rules, alert storage, the alerts API, or the confirmation flow;
- changing the frontend or OpenAPI contracts;
- changing watchlist, chart, news, or coin overview tools;
- fixing behavior in languages other than English beyond what the shared prompt rules provide;
- changing the eval pass-rate threshold, trajectory matching, or the CI job;
- implementing the planned sources, calculation, compaction, or feedback changes.

## Impact

- Backend: assistant system prompt, alert tool argument descriptions, and alert matching logic in the alert tools; unit tests for alert matching.
- Evals: new scenarios, stub data with several alerts for one coin, and an optional per-turn scenario field asserting that no proposal was captured.
- No database, API, OpenAPI, Orval, or frontend changes.
