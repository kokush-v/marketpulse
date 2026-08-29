## Overview

The assistant is a backend-owned, authenticated feature. LangGraph coordinates a bounded conversation graph and Groq provides model inference. The model never receives database credentials, Supabase secrets, provider keys, or direct network/database tools. It can only request explicitly registered application tools.

The first delivery is web-only: a product-wide widget opens a compact conversation UI, and a dedicated protected page provides the same chat capability with conversation history.

## Functional Plan

### Phase 1: Conversation foundation

- protected assistant API, widget, and dedicated page
- user-owned conversation and message persistence
- three model-generated, context-aware follow-up prompts for every assistant response
- streaming or incremental assistant responses where supported by the selected API contract
- LangGraph conversation flow with bounded tool-call iterations and a clear fallback for invalid model output or provider failures

### Phase 2: Read tools

- `get_coin_overview`: normalized description and current market summary for a named coin or symbol
- `get_coin_news`: latest available news for a named coin or symbol
- `list_watchlist_assets`: authenticated user's saved assets
- `list_alerts`: authenticated user's alerts and readable status summaries
- `get_price_chart_data`: normalized price-series data for one to five named coins and a requested period

### Phase 3: Action tools

- `add_watchlist_asset`: add a chosen asset, using existing duplicate prevention
- `create_alert`: create an alert only after the agent has collected a valid supported scenario and required configuration
- `update_alert`: modify one of the authenticated user's alerts with valid requested fields
- `pause_alert` and `resume_alert`: change the lifecycle state of an owned alert
- `remove_watchlist_asset` and `delete_alert`: initiate, then execute only after an explicit in-chat confirmation

### Phase 4: Quality and guardrails

- visible loading, empty, and recoverable error states
- tool-call audit information suitable for debugging without storing secrets or raw provider internals
- focused authorization, validation, confirmation, and provider-failure tests

Caching is deliberately deferred; tools initially reuse the established market-data and news service behavior.

## LangGraph Flow

The graph should load the authenticated conversation context, invoke the Groq model with a tool catalog and scoped context, execute validated tools when requested, append tool outcomes, and continue until it produces a user-facing response or reaches a bounded stop condition. Tool execution must occur in the backend service layer, not in the browser.

The graph MUST distinguish a proposed destructive action from a confirmed action. A request such as “delete my BTC alert” creates a pending confirmation containing the intended action and target. Only an unambiguous confirmation referring to that pending action may invoke the destructive tool. Cancellation, expiration, or a changed target clears the pending confirmation and performs no mutation.

## Tool Contract Principles

Each tool should be small, typed, and purpose-specific. Inputs are validated with Pydantic schemas; outputs are normalized, compact, and safe for a model to summarize. Tools call the existing feature services or repositories behind those services rather than duplicating domain logic.

Read-tool outputs expose only fields needed to answer the user's request. They must not include internal database IDs, provider asset IDs, category lists, raw market-cap values, or redundant echoed query values. Coin overview returns the coin name and symbol, optional description, current price, 24-hour percentage change, and market-cap rank. Coin-news results retain article data needed to summarize and link news. Watchlist and alert lists use user-readable labels and summaries without resource IDs.

Every user-owned tool derives the user from the validated request identity. The model must not supply or select a user identifier. Tools must return an ownership-safe not-found or forbidden result for resources outside the authenticated user's scope.

The agent should ask a follow-up question when a requested action lacks required fields. It must not infer an alert threshold, timing behavior, asset, or deletion target from ambiguous prose. Existing alert scenarios and validation rules remain authoritative.

Assistant responses use concise prose and Markdown lists by default. A Markdown table is reserved for cases where the user requests one or where comparing multiple same-shaped records is materially clearer. A single coin summary, news explanation, or ordinary answer must not be presented as a table solely because structured data was returned by a tool.

## Chart Tool And Message Contract

`get_price_chart_data` accepts one to five coin names or symbols and an optional period of `24h`, `7d`, `30d`, or `1y`; `7d` is the default. The tool resolves provider identifiers internally and returns only user-facing series names, symbols, normalized timestamp/price points, and the selected period. A request for more than five coins or an ambiguous symbol requires a concise follow-up question rather than an inferred chart.

The Ruby market-data service obtains historical data from CoinGecko behind a dedicated server-side endpoint. FastAPI remains the trusted boundary that calls this service and normalizes failures. The browser never calls the Ruby service or CoinGecko directly.

When the graph uses the chart tool, the assistant response persists an optional chart payload alongside its Markdown content and suggested replies. The payload contains the period and one to five labeled series of time/price points, but no provider or database identifiers. The frontend renders this payload as an interactive Recharts line chart below the assistant text. The model also receives chart data and is instructed to give a concise, non-advisory analysis.

Chart revisions are ordinary conversational turns. A request such as “remove ETH” or “compare BTC and ETH” causes the agent to call the chart tool with the newly requested series and returns a new assistant message and chart card; historic messages and their charts remain unchanged.

## Data Model

Add user-owned persistence for:

- `assistant_conversations`: conversation identity, owning user, title/summary if needed, and timestamps
- `assistant_messages`: ordered user, assistant, and tool-result messages associated with one conversation
- assistant messages retain three validated suggested replies for the next user turn
- assistant messages may retain an optional validated chart payload for an interactive chart card
- `assistant_pending_actions`: short-lived pending destructive action, target reference, serialized validated input, creation time, expiry, and resolution status

Messages should retain only the data needed to render a conversation and safely continue it. Secrets, access tokens, provider request headers, and raw internal errors MUST NOT be persisted in messages or tool records.

Conversation title updates and deletion are scoped by both conversation ID and authenticated user ID. Deleting a conversation relies on the existing database foreign-key cascade to remove its messages and any pending actions.

Conversation-history activity ordering is based on message activity, rather than a title-only update. Renaming therefore leaves an entry in its current place in the history.

When a titleless conversation receives its first non-empty user message, the backend derives its initial title from the first three whitespace-delimited words of that message. If the message contains additional words, the derived title ends with `...`. An explicitly supplied title or a title saved through Rename is never replaced by this automatic derivation. The derived title must respect the existing conversation-title length limit.

## API and Frontend

The backend will expose protected endpoints to create/list/load conversations and send a message to a conversation. The message endpoint returns an assistant reply, exactly three short model-generated suggested replies, and structured UI-safe metadata for pending confirmations or completed actions. Suggested replies are persisted with the assistant message so the widget and page render the same history. The backend validates that suggestions are non-empty, distinct, and suitable as ordinary user messages; it falls back to safe context-neutral prompts if the model response is malformed. Frontend code uses the generated API client after OpenAPI regeneration.

Assistant-message responses additionally expose an optional validated chart payload. The frontend uses it to render an accessible, responsive line chart with one to five series and a period label. No raw provider IDs are returned to the browser.

The widget and page use the same conversation API. A user can open a new conversation from either surface and continue an existing one on the dedicated page. Both surfaces show clear sending, error, empty, and pending-confirmation states. Each assistant message renders its three suggestions as in-chat buttons; selecting one places its text into the same message-send flow as a manually composed request and hides that message's quick-reply controls immediately. The chat confirmation is rendered as a conversational action (for example, Confirm / Cancel controls attached to the assistant message), not a modal.

The dedicated conversation history provides a context menu for each conversation entry. It contains only Rename and Delete actions. Rename swaps that entry for an inline title input with Save and Cancel controls. Delete presents an inline Confirm / Cancel state on the same entry; the delete endpoint is called only after confirmation. The API exposes protected update-title and delete-conversation operations and the frontend regenerates its client from OpenAPI.

Newly created titleless conversations display their derived title after the first user message is saved, so the same title is immediately visible in the dedicated history and any other assistant surface.

## Failure, Security, and Limits

- Groq timeouts, rate limits, malformed responses, or unavailable models return a safe recoverable chat error and do not execute a mutation.
- Domain provider failures are translated through the established services into safe tool outcomes.
- Tool-call count, request size, and conversation context passed to the model are bounded to protect availability and cost. Exact limits are implementation configuration, not a product contract.
- All database and network I/O in the assistant flow is asynchronous.
- Groq credentials remain backend-only and are loaded through approved server configuration.

## Migration and Rollback

The implementation requires an Alembic migration for assistant conversations, messages, and pending actions. The new functionality is additive and can be disabled by removing its frontend entry points or server configuration; it does not alter existing alert or watchlist records.
