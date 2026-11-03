## 1. Backend

- [x] 1.1 Add input and result contracts for conversion, price change, and target distance calculations.
- [x] 1.2 Implement `convert_crypto_amount` (coin to USD and USD to coin) with `Decimal` arithmetic and result rounding.
- [x] 1.3 Implement `calculate_price_change` for `24h`, `7d`, `30d`, and `1y` from historical price data.
- [x] 1.4 Implement `calculate_target_distance` for a user-supplied USD target and for the user's active price alerts, including percent-alert target derivation.
- [x] 1.5 Return clarification results for missing, invalid, or ambiguous inputs and a list of matching alerts when several qualify.
- [x] 1.6 Record `MarketPulse knowledge` sources with update time and staleness for each successful calculation.
- [x] 1.7 Register the calculation tools and extend the system prompt with calculation, clarification, and decline rules.

## 2. Backend Tests

- [x] 2.1 Unit tests for conversion in both directions, rounding, and non-positive amounts.
- [x] 2.2 Unit tests for price change per period and missing history.
- [x] 2.3 Unit tests for target distance: user target above and below current price, fixed-price alert, percent alert above and below, several matching alerts, news or paused alert only, another user's alert not visible.
- [x] 2.4 Unit tests for sources and staleness recorded by calculation tools.
- [x] 2.5 Eval scenarios: conversion, price change, distance to target, distance to a single alert, several matching alerts, missing amount triggers no tool call, unsupported calculation triggers no tool call.

## 3. Validation

- [x] 3.1 `docker compose exec -T backend uv run ruff check .` and `uv run ruff format --check .`.
- [x] 3.2 `docker compose exec -T backend uv run pytest tests/unit/features/ai_assistant`.
- [ ] 3.3 `docker compose exec -T backend make test-ai-eval`.
- [x] 3.4 `openspec validate add-assistant-calculation-tools --strict`.
