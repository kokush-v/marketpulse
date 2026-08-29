## Summary

Add a protected web AI assistant for MarketPulse. Authenticated users can open a compact chat widget from product screens or use a dedicated assistant page, ask about cryptocurrency market data and news, and manage their own MarketPulse resources through conversational requests.

## Problem

MarketPulse data and workflows are currently accessed only through separate product screens. Users who want an explanation of a coin, recent news, or help creating an alert must know which screen and form to use. There is no conversational interface that can combine product context with safe user-owned actions.

## Proposed Solution

Introduce an `ai-assistant` capability backed by LangGraph and Groq. The backend-owned agent will use explicitly defined tools that call existing application services for market data, news, watchlists, and alerts. The agent will return clear natural-language results and can perform permitted operations only in the authenticated user's scope.

The web experience will provide a persistent entry widget and a dedicated chat page. Destructive operations require an explicit in-chat confirmation before their corresponding tool can run; no modal confirmation UI is introduced.

## Scope

Affected domains:

- `ai-assistant` (new)
- `auth`
- `market-data`
- `news`
- `watchlists`
- `alerts`
- `api-client-generation`

Primary workflows:

- an authenticated user opens the assistant widget or dedicated assistant page and sends a message
- a user asks for a coin description, current market information, or recent coin news
- a user asks the assistant to list, create, update, pause, resume, or delete personal alerts
- a user asks the assistant to add or remove a personal watchlist asset
- the agent gathers missing information for a requested action and reports the result in chat
- the agent asks for an explicit in-chat confirmation before deleting an alert or removing a saved asset

In scope:

- protected web chat widget and dedicated assistant page
- persisted user-owned conversations and messages, so the widget and page can continue the same conversation
- an initial conversation title derived from the first user message when the user has not named the conversation
- three persisted, context-aware quick replies attached to each assistant response
- stable conversation-history ordering when a title is renamed
- collapsing quick-reply controls after the user selects one
- user-owned conversation rename and deletion controls in the dedicated conversation history
- a LangGraph orchestration flow using Groq as the model provider
- explicit backend tools for safe read access to coin information, market data, news, alerts, and watchlist data
- compact read-tool payloads that exclude internal resource identifiers and redundant provider metadata
- readable assistant responses that use Markdown tables only when they materially improve comparison or scanning
- agent-generated interactive price charts and chart analysis for one to five requested coins
- explicit backend tools for permitted user-owned alert and watchlist operations
- tool input validation, authenticated ownership enforcement, provider-failure handling, and user-safe chat errors
- conversational confirmation state for destructive actions, including cancellation and expiration
- backend API contracts and regenerated frontend client support
- a functional tool catalog and staged delivery plan in the design

## Non-Goals

- Telegram chat integration or Telegram agent controls
- caching strategy or cache infrastructure for model, market-data, or news requests
- investment advice, trading execution, price predictions, or portfolio recommendations
- arbitrary database access, raw SQL, shell execution, or generic external web browsing by the model
- autonomous scheduled agent actions
- replacing existing watchlist, alerts, market-data, or news screens
- changing existing alert semantics, market-overview behavior, or news contracts
- editing or mutating a previously sent chart in place; each user request creates a new assistant message

## Impact

The change adds a new protected backend feature, database persistence for chat state and pending destructive confirmations, a Groq integration, frontend chat surfaces, and OpenAPI/Orval updates. Existing domain services remain the trusted source of data and mutations; provider secrets and user authorization stay on the backend.
