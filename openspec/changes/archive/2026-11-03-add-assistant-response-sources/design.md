## Context

Assistant responses are produced by `AssistantGraph` over read, chart, watchlist, and alert tools. Chart data already follows a capture-and-persist pattern: tools write into `ChartPayloadCapture`, the graph exposes it, and `service.py` stores it in the `assistant_messages.chart_payload` JSONB column, returned as `AssistantMessageResponse.chart_payload`. Market overview responses carry `source` and `generated_at`; news articles carry `source`, `url`, and `published_at`. Asset search results carry no timestamp.

## Decisions

### Source model

Each source entry has:

- `kind`: `news` or `marketpulse`;
- `label`: publisher name for news, `MarketPulse knowledge` otherwise;
- `title`: article title for news; a short description of the data for `marketpulse` sources (for example "BTC price", "Your alerts");
- `url`: article URL for news; `null` otherwise;
- `updated_at`: article publication time for news, data update time for market data, `null` for watchlist and alert data and when unknown;
- `stale`: `true` when market data is older than the freshness threshold or its update time is unknown, otherwise `false`.

Sources are deduplicated per message (news by URL, `marketpulse` sources by title).

### Capture and persistence

Add a `SourcesCapture` alongside `ChartPayloadCapture`. Tools append source entries for the data they actually return to the model; tool errors and empty results add no source. The graph response exposes the collected sources, and the service persists them in a new nullable JSONB column `assistant_messages.sources`. Messages without sources store `null` and render no block. Existing messages are unaffected.

### Tool results carry source metadata

Tool result payloads given to the model include the same `updated_at` and `stale` values so the model can phrase the warning. Internal identifiers remain excluded per the existing read-tool data exposure requirement.

- `get_coin_overview`: update time from the market overview `generated_at`; for the search fallback, which has no timestamp, `updated_at` is `null` and the source is stale (builder may use a timestamp from the market data service if one is available without new provider calls).
- `get_price_chart_data`: update time of the latest returned point.
- `get_coin_news`: one news source per returned article.
- `list_watchlist_assets`, `list_alerts`: one `marketpulse` source without update time, never stale.

### Freshness threshold

New setting `ASSISTANT_MARKET_DATA_MAX_AGE_SECONDS`, default 900. Staleness is computed in the backend, not by the model.

### Prompt rules

The system prompt is extended to: state facts and figures only from tool results in the current conversation; warn explicitly in the response when a tool result is marked stale; say clearly that it cannot answer when tools return no data or the question is outside MarketPulse data; continue to describe MarketPulse capabilities in product language. The prompt must not ask the model to write source lists, because the UI block renders them.

### API contract

`AssistantMessageResponse` gains `sources: list[AssistantMessageSourceResponse]` (empty list when none). The frontend uses the regenerated Orval types.

### Frontend

`assistant-chat.tsx` renders a compact sources block under assistant messages that have sources: label, title, relative or formatted time, a stale marker, and an external link (new tab, `rel="noopener noreferrer"`) only for news. Shared by widget and page through the existing chat component.

## Risks

- The model may still phrase unsupported claims; eval scenarios and prompt rules reduce but do not eliminate this.
- Search fallback results are always marked stale until the market data service exposes a timestamp for them.

## Rollback

Revert the prompt and UI changes; the nullable column can stay or be dropped by a down migration without affecting other message data.
