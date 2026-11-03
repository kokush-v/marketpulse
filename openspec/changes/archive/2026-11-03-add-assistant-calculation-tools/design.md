## Context

Assistant tools live in `app/features/ai_assistant/tools/` and return `ToolResult` payloads with statuses such as `ok`, `clarification_needed`, and `error`. Asset and alert resolution helpers with clarification results already exist in `tools/shared.py` (`resolve_search_asset`, `resolve_alert`). Market prices are USD. Price alerts store `trigger_mode` (`currency` or `percent`), `threshold_value`, and for percent alerts a `baseline_price`; the scenario (`price_above` / `price_below`) gives the direction.

## Decisions

### Tools

New module `tools/calculation_tools.py`, registered with the read tools. All tools are read-only and never create pending actions.

1. `convert_crypto_amount(coin, amount, direction)` — `direction` is `coin_to_usd` or `usd_to_coin`; `amount` must be greater than zero. Returns the input amount, the converted amount, the coin symbol, the USD rate used, and the rate's update time.
2. `calculate_price_change(coin, period)` — `period` is one of `24h`, `7d`, `30d`, `1y`. Uses the same historical price data as the chart tool. Returns start price, end price, their times, absolute USD change, and percentage change.
3. `calculate_target_distance(coin, target_price | alert)` — exactly one of `target_price` (USD, greater than zero) or `alert` (a user reference to an alert) is required. Returns the current price, the target price, the target's origin (user target or the alert summary), the USD difference, the percentage difference relative to the current price, and the direction (above or below the current price).

### Alert targets

- Only the authenticated user's alerts are considered, through the existing alert service.
- Only active price alerts qualify. News alerts and paused alerts are not used; when the reference matches only those, the tool returns a clarification stating no active price alert matches.
- Exactly one match: used directly. Several matches: `clarification_needed` listing the matching alerts (coin, rule, schedule) for the user to choose; no calculation is returned.
- Fixed-price alert target = `threshold_value`. Percent alert target = `baseline_price × (1 + threshold/100)` for `price_above` and `baseline_price × (1 − threshold/100)` for `price_below`.

### Clarification and validation

- Missing or non-positive amounts, missing target, both target and alert given, unsupported period, or unresolved/ambiguous coin return `clarification_needed` with a message and candidate matches where applicable; argument schema validation rejects invalid enums.
- Market data failures return the existing safe error result.

### Precision

Calculations use `Decimal`. USD values are rounded to 2 decimals for prices of at least 1 USD and up to 8 significant decimals below 1 USD; coin amounts up to 8 decimals; percentages to 2 decimals. Rounding happens only in the returned result.

### Sources and staleness

Each successful calculation records a `MarketPulse knowledge` source with the update time of the market data used and the staleness flag from `add-assistant-response-sources`; the tool result carries `stale` so the model warns the user.

### Prompt rules

Extend the system prompt: use the calculation tools for any conversion, percentage change, or distance to a target or alert; never compute these numbers itself; ask for missing inputs; when the user asks for a calculation not covered by a tool, say it cannot calculate that.

## Risks

- The model may still answer arithmetic directly; eval scenarios cover tool selection for each calculation and the decline path.
- Percent alerts created before `baseline_price` was stored cannot produce a target; the tool returns a safe error for such alerts.

## Rollback

Unregister the tools and revert the prompt; no data changes are involved.
