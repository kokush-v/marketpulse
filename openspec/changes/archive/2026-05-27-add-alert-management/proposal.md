## Summary

Add the first dedicated `alerts` capability for authenticated users so they can create, view, edit, pause, resume, and delete personal crypto alerts from a standalone `Alerts` workspace. The first version uses a step-by-step, chart-first alert authoring flow with three clear scenarios only: `Price above`, `Price below`, and `News`. The user starts from watchlist coins, can add a missing coin into the watchlist from the same flow, and for price alerts defines the trigger through a single value input paired with a `% / $` toggle and an interactive price chart with `1D`, `1W`, and `1M` time scopes. Alerts also define a time behavior: either one-time execution or once-per-day recurring behavior within a chosen start and end date range.

## Problem

MarketPulse product scope already calls out alert rules and notification history, but there is no approved contract that defines how users manage alerts, what rule types are supported, or how the frontend should present an alert creation flow that feels simple, modern, and understandable to regular users.

Without an explicit `alerts` capability, implementation would risk:

- creating incompatible backend and frontend assumptions about alert rule structure
- mixing alert authoring behavior into unrelated watchlist or notification contracts
- introducing a confusing, overly generic builder flow that does not match the intended product UX
- leaving future evaluation and notification work without a consistent alert data model

## Proposed Solution

Introduce a focused `alerts` capability with a protected alerts-management API and a dedicated `Alerts` workspace for authenticated users.

This change defines:

- user-owned alerts with full create, list, edit, pause, resume, and delete behavior
- alert scenarios for:
  - price moving above a trigger value
  - price moving below a trigger value
  - new article publication for a selected coin
- a watchlist-first alert authoring experience that starts from the user's saved watchlist coins
- an inline path to add a missing coin into the watchlist without leaving alert creation
- a stepper-based flow that guides the user through one alert-authoring step at a time
- a chart-first alert authoring experience that starts with coin selection and then leads the user into one scenario at a time
- a single trigger-value control for price alerts with a `% / $` toggle
- interactive chart time scopes for `1D`, `1W`, and `1M`
- visible trigger placement on the chart while the alert is being configured
- percentage-based price rules interpreted relative to the current price at alert creation time
- alert time behavior for:
  - one-time alerts
  - once-per-day recurring alerts with a start and end date
- alert status behavior for active and paused alerts
- a dedicated `Alerts` tab that displays user alerts as cards with readable rule summaries and lifecycle actions
- stable request and response contracts suitable for OpenAPI and Orval-generated frontend clients

This change intentionally defines alert authoring and lifecycle management only. Background evaluation, scheduled alert checking, and creation of notification-history records when rules trigger will be specified in a follow-up `background-jobs` and/or `notifications` change.

## Scope

Affected domains:

- `alerts`
- `watchlists`
- `api-client-generation`

Primary user workflows:

- authenticated user opens the `Alerts` workspace and sees all personal alerts as cards
- authenticated user starts alert creation by choosing a coin from the personal watchlist
- authenticated user adds a missing coin into the watchlist from the alert flow and continues without leaving that flow
- authenticated user picks one scenario from `Price above`, `Price below`, or `News`
- authenticated user moves through the flow one step at a time with a visible stepper
- authenticated user uses a chart-first price flow with a `% / $` toggle, `1D / 1W / 1M` scope switcher, and a visible trigger line for price alerts
- authenticated user edits an existing alert through the same step-by-step flow
- authenticated user chooses whether the alert is one-time or daily recurring
- authenticated user picks a start and end date for daily recurring alerts through a calendar UI
- authenticated user pauses, resumes, or deletes an alert

In scope:

- protected alerts-management endpoints for authenticated users
- user-owned alert persistence and ownership rules
- alert status lifecycle for active and paused alerts
- `price_above` and `price_below` scenarios
- absolute-value and percentage-based trigger input for price scenarios
- percentage-based price rules anchored to the current price at creation time
- coin-news subscription rules that target any new article for a selected coin
- one-time alert scheduling behavior
- once-per-day recurring behavior scoped to a chosen start and end date
- alerts coin picker limited to the authenticated user's watchlist assets
- an inline add-to-watchlist action in the alert authoring flow
- a stepper-based create/edit experience
- a chart-first create/edit experience for price alerts
- price-chart scope switching between `1D`, `1W`, and `1M`
- trigger visualization on the chart while the user configures price alerts
- a calendar-based start-date and end-date selector for recurring alert duration
- a clear scenario-selection step with only three user-visible choices
- alerts listing UI with card actions for edit, pause/resume, and delete
- explicit loading, empty, and error states for the alerts workspace
- OpenAPI updates and Orval regeneration for the new alert endpoints

## Non-Goals

- background jobs or scheduled alert evaluation
- actual trigger execution and notification-history record creation
- Telegram delivery
- cooldowns, spam prevention beyond the explicit once-per-day recurring limit, or multi-trigger throttling policies
- multi-condition or boolean-rule composition in the first version
- advanced technical charting tools that go beyond alert placement and trigger preview
- a large persistent builder-notes side panel that competes with the main flow for screen space

## Impact

This change establishes the first stable contract for alert management in MarketPulse and creates the data and API foundation that future trigger-evaluation and notification-delivery changes can build on. It also defines a user-facing alerts workspace and a focused, exchange-inspired alert authoring flow that prioritizes clarity over generic flexibility, keeps users anchored to their watchlist context, and guides them forward through explicit steps.
