## Overview

This change defines the first alert authoring and management contract for MarketPulse. It adds a protected alerts-management API and a dedicated `Alerts` workspace where authenticated users can manage personal crypto alerts. The first version covers authoring, persistence, lifecycle management, and user-selected alert time behavior only. It does not define scheduled evaluation or trigger delivery.

## Authorization And Ownership

- All alert-management routes SHALL require an authenticated user session.
- The backend SHALL derive the current user from the validated Supabase access token and the local `users` record.
- Alert records SHALL be user-owned resources enforced through backend ownership filters and queries.
- Alert-management requests SHALL NOT accept or trust client-supplied user identifiers.

## Alert Rule Model

The first version supports these condition types:

- price above an absolute currency value
- price below an absolute currency value
- price above a percentage threshold from a captured baseline price
- price below a percentage threshold from a captured baseline price
- any new article for a selected coin

Each alert belongs to one selected coin context and SHALL represent one user-visible scenario at a time:

- `Price above`
- `Price below`
- `News`

The implementation may choose the exact API payload shape, but it must preserve these observable rules:

- the frontend authoring flow presents only the three supported scenarios
- price scenarios can be expressed in either absolute currency or percentage mode
- the backend validates every supported scenario and trigger mode explicitly
- persisted data preserves enough structure to support future evaluation without ambiguous reconstruction

Each alert also carries one time-behavior mode that applies to all alert types:

- `one_time`: the alert is intended to trigger once and then stop
- `daily_recurring`: the alert may trigger at most once per calendar day while it remains inside a configured start and end date range

For `daily_recurring` alerts:

- the user chooses both a `start date` and an `end date`
- future evaluation work must enforce no more than one successful trigger per day
- after a successful trigger on a given day, the alert becomes eligible again on the next day if the alert is still inside its active date window

## Percentage Rule Baseline

Percentage-based rules are anchored to the current coin price at the moment the alert is created or fully edited.

That means:

- creating a new percentage-based alert captures a baseline price for the selected coin
- fully editing an existing alert and keeping or changing a percentage-based condition captures a new baseline price using the current market price at edit time
- future alert evaluation work must compare live prices against the stored baseline and threshold, rather than against day-open price or a frontend-provided reference

Because this behavior depends on current price data, backend implementation should source the baseline from trusted backend market-data access rather than trusting a value provided by the frontend.

## API Contract Notes

The alerts API must support:

- list all alerts for the authenticated user
- create an alert
- update an alert
- pause an alert
- resume an alert
- delete an alert

Response contracts should expose:

- alert identifier
- selected coin identity and display name
- current status
- structured rule data for edit flows
- structured time-behavior data for edit flows
- readable rule summary text for cards
- created-at and updated-at timestamps

Because this introduces new backend contracts, OpenAPI output and Orval-generated frontend clients must be updated as part of implementation.

## Frontend Workspace And Authoring Flow

- The frontend SHALL provide a dedicated protected `Alerts` workspace or tab for authenticated users.
- The workspace SHALL display alerts as cards that show the coin name, a readable description of the rule set, and actions for pause/resume, edit, and delete.
- The workspace SHALL provide explicit loading, empty, and error states.
- The create and edit flows SHALL use a visible stepper that communicates progress through the alert-authoring sequence.
- The create and edit flows SHALL guide the user through a clear sequence:
  - choose a coin from the authenticated user's watchlist
  - add a missing coin to the watchlist when necessary
  - choose one scenario from `Price above`, `Price below`, or `News`
  - choose a time-behavior mode
  - configure the selected scenario
- The frontend SHALL allow the user to choose between `one-time` and `daily recurring` behavior for all alert types.
- The frontend SHALL provide a date-range picker for recurring alerts using the project's shadcn/ui component stack.
- The frontend implementation SHOULD use the requested stepper component pattern and MAY use `@reui/c-stepper-9` through the local shadcn integration workflow if it fits the existing component stack.
- Price alert flows SHALL show an interactive price chart as the primary context for authoring.
- Price alert flows SHALL provide one trigger-value control with a `% / $` toggle aligned to that input.
- Price alert flows SHALL provide scope switching for `1D`, `1W`, and `1M`.
- Price alert flows SHALL render the current trigger value directly on the chart while the user configures it.
- The frontend SHOULD follow modern exchange-inspired interaction patterns that prioritize clarity and fast recognition over generic form-builder flexibility.
- The frontend SHOULD use lightweight motion for step transitions, chart-state changes, and scenario selection when it helps the user maintain context.
- Supporting guidance SHOULD be presented inline or contextually rather than as a large persistent notes panel that competes with the main flow for space.
- The create and edit flows SHALL allow full alert edits, including changing the coin, scenario, and trigger mode.

This change does not prescribe a visual library or interaction choreography beyond these user-visible behaviors.

## Notification Relationship

The product intent for these alerts is eventual delivery into notification history, with Telegram delivery deferred.

However, this change does not define:

- scheduled evaluation of alerts
- event-driven trigger execution
- notification-history record creation
- notification read/unread workflows

Those behaviors should be introduced in a follow-up change once the alert-management contract is implemented.

## Data Model And Persistence

This change requires persistent user-owned alert storage.

The implementation should account for:

- selected coin identity
- user ownership
- alert status such as active or paused
- one stored alert scenario per alert
- one stored time-behavior mode per alert
- recurring start and end dates when the alert is not one-time
- enough state to support future once-per-day recurring enforcement
- baseline price storage for percentage-based conditions
- timestamps needed for management flows

The exact relational shape is an implementation choice, but it must support future evaluation work without rewriting the user-facing contract.

## Failure Handling

The system must account for:

- unsupported rule types
- missing coin selection
- attempts to create an alert for a coin outside the user's watchlist when the flow is watchlist-scoped
- invalid numeric threshold values
- invalid or incomplete recurring date windows
- end dates earlier than start dates
- inability to resolve current price when creating or editing percentage-based alerts
- attempts to access another user's alert

In all such cases, the backend should return frontend-safe validation or application errors without exposing provider secrets or internal diagnostics.

## Risks

- Percentage-based rules depend on trustworthy current-price lookup at create/edit time, which introduces a backend dependency on market-data availability.
- A chart-first authoring flow can become harder to keep consistent if the backend contract exposes trigger data in a way that is too generic or too UI-specific.
- Coupling alert creation to watchlist membership means the watchlist add flow must feel fast and predictable, or users may perceive alert creation as blocked.
- Time-window behavior introduces more alert state that future background evaluation work must interpret consistently across time zones and day boundaries.

## Rollback

If the feature needs to be rolled back after implementation, rollback will require removing the alerts-management routes, frontend workspace integration, and any alert-related schema changes through the project's normal migration rollback process.
