## Summary

Move market arithmetic out of the language model. Add deterministic assistant tools for converting between a coin amount and USD, calculating a coin's percentage price change over a period, and calculating the distance from the current price to a target price or to one of the user's price alerts. Each tool returns its result together with the inputs it used. The assistant asks for missing information instead of guessing and declines calculations no tool supports.

## Problem

Apart from the chart summary, the assistant computes conversions, percentage changes, and distances to alert thresholds by itself. Language models make arithmetic mistakes and can silently mix stale or invented inputs, so users can receive confident but wrong numbers.

## Proposed Solution

Add three read-only calculation tools that compute results in backend code from MarketPulse market and alert data:

- **Conversion:** coin amount to USD and USD amount to coin, returning the result, the USD rate used, and its update time.
- **Price change:** percentage and absolute USD change of one coin over `24h`, `7d`, `30d`, or `1y`, returning start and end prices and their times.
- **Distance to target:** difference in USD and percent between the current price and either a user-supplied USD target price or the target price of one of the user's active price alerts (fixed-price alerts use the threshold; percent alerts derive the target from the alert's baseline price).

Results produce `MarketPulse knowledge` sources with update times and staleness as defined by `add-assistant-response-sources`. The system prompt requires these tools for any such calculation, clarification when inputs are missing or ambiguous, and an explicit "cannot calculate" answer for calculations no tool supports.

## Scope

Affected domain: `ai-assistant`.

- three calculation tools with input validation and clarification results;
- alert target selection: one matching active price alert is used directly; several matches return a clarification listing them for the user to choose; news alerts are not applicable;
- prompt rules for using calculation tools, asking for missing inputs, and declining unsupported calculations;
- backend unit tests and eval scenarios.

## Non-Goals

- currencies other than USD (deferred to a future fiat exchange rates change);
- historical "what if I had bought" profit calculations, averages across coins, portfolio valuation, or other calculations not listed above;
- new market data providers, new persisted data, or database changes;
- API contract or frontend changes beyond the sources block from `add-assistant-response-sources`;
- changing alert evaluation logic.

## Impact

- Backend: new tool module and contracts, tool registration, system prompt update.
- Depends on `add-assistant-response-sources` (sources and staleness) and `add-ai-assistant-tool-evals` (eval scenarios).
- No database, OpenAPI, or Orval changes.
