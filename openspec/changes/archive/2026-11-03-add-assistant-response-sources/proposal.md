## Summary

Show where every assistant answer about prices, market data, news, and personal records came from. Each assistant message gets a persisted sources block rendered under the message, the assistant warns when market data is stale, and the assistant states that it cannot answer instead of answering from unsupported knowledge.

## Problem

Assistant answers about prices and news do not reliably show their origin or freshness. Coin overview results reach the model without a source or update time, news article links are shown only if the model decides to include them, and nothing prevents the model from answering from its own general knowledge. Users cannot tell whether a number is current or whether a statement is backed by MarketPulse data.

## Proposed Solution

- Read tools return source metadata with their results: a source label, an update or publication time, and a link when one exists.
- The backend collects source metadata from the tools actually called for a response and persists it with the assistant message, the same way chart payloads are persisted.
- The message API exposes the sources; the frontend renders a sources block under the assistant message in both the widget and the assistant page.
- News sources show the publisher, title, publication time, and article link. Prices, market data, watchlist, and alert data are labeled `MarketPulse knowledge` with an update time where applicable and no link.
- Market data older than a configurable freshness threshold (default 15 minutes) is still answered, but the assistant warns about it in the response and the source is marked stale.
- The assistant answers facts and figures only from tool results. When tools return no data or the question is outside MarketPulse data, the assistant says it cannot answer. Describing MarketPulse capabilities remains allowed.

## Scope

Affected domain: `ai-assistant`.

- source metadata for coin overview, coin news, price chart, watchlist list, and alert list tool results;
- persisted per-message sources and their API exposure;
- sources block in the assistant chat UI with loading-independent rendering of persisted messages;
- stale market data warning with a configurable threshold;
- refusal to answer without supporting data;
- backend tests, eval scenarios in the suite from `add-ai-assistant-tool-evals`, migration, OpenAPI/Orval regeneration.

## Non-Goals

- deterministic calculation tools and calculation clarifications (change `add-assistant-calculation-tools`);
- links to external provider pages for prices or market data;
- refusing to answer when data is stale;
- translating source labels;
- a separate sources page or source filtering;
- changing news or market data providers or their caching.

## Impact

- Database: new nullable column on `assistant_messages` for sources (Alembic migration).
- API: assistant message responses gain a `sources` field; Orval client regeneration and frontend updates required.
- Backend: tool result contracts, response orchestration, system prompt, and a new freshness setting.
- Frontend: new sources block in the assistant chat message.
