## Summary

Improve alert runtime behavior across lifecycle, scheduler architecture, and market-overview freshness so alerts re-arm correctly, recurring alerts can emit multiple meaningful same-day events, alert jobs are split by family, and market-overview-backed alert context stays fresher.

## Problem

The current alert runtime behavior creates three connected product gaps:

- one-time alerts stop being eligible after they fire, but they still appear active in the UI because they do not transition into a visible paused state
- recurring alerts are limited to one trigger per calendar day, which is too coarse for price movement and news-following workflows where multiple distinct events can happen on the same day
- scheduled alert evaluation still runs through one shared scheduler, one shared cursor, and one branching service, which makes price and news alert behavior harder to evolve independently
- market-overview snapshots that support selected-coin context may remain fresh for too long and stale for far too long, which weakens timeliness for alert-adjacent market tracking workflows

This leaves users without a clear lifecycle for consumed one-time alerts, prevents recurring alerts from delivering timely follow-up notifications when the market or news stream changes again later that day, and keeps the alert runtime architecture and supporting market context less timely and less maintainable than needed.

## Proposed Solution

Change alert runtime behavior in one focused upgrade:

- auto-pause one-time alerts immediately after a successful trigger so the consumed state is visible in the product
- when a user resumes a fired one-time alert, re-arm it from the current state at resume time instead of reusing the old baseline
- update recurring price alerts so each successful trigger recalibrates the next trigger threshold from the current price, allowing additional same-day triggers when the market moves enough again
- update recurring news alerts so each distinct newly available article may trigger its own notification during the active recurring window, including multiple articles on the same day
- split scheduled alert evaluation into dedicated price-alert and news-alert background jobs with independent cursors and catch-up paths
- restructure alert evaluation around a Factory Method-based creator flow so shared orchestration remains centralized while concrete alert families create their own evaluator products
- reduce market-overview snapshot freshness to fifteen minutes and stale fallback retention to thirty minutes so market-overview-backed alert context stays fresher
- update scheduler, market-data, and notification-history requirements so recurring occurrences remain distinct and observable during normal runs and catch-up runs while market context freshness remains aligned with alert needs

## Scope

- `alerts` domain behavior for one-time and recurring alert lifecycle rules
- recurring price and news trigger semantics
- protected API and frontend-visible alert status behavior needed to represent consumed one-time alerts and resumed alerts correctly
- notification-history behavior for multiple same-day recurring occurrences
- scheduled evaluation and catch-up behavior for recurring alerts that may re-trigger multiple times on the same day
- background scheduling architecture for separate price and news alert jobs
- market-overview snapshot freshness and stale retention behavior that supports alert-adjacent selected-coin context

## Non-Goals

- introducing new alert types
- changing the five-minute scheduler cadence
- redesigning Telegram linking or general notification preferences
- adding user-configurable per-alert cooldown controls in this change
- redesigning the overall alert authoring flow beyond the timing and lifecycle behavior required by this upgrade
- changing asset-search cache TTL
- adding caching for coin news
- introducing more alert scheduler families beyond price and news in this change

## Impact

- Affected domains: `alerts`, `notifications`, `background-jobs`, `market-data`
- Backend work will require alert lifecycle and recurring-trigger persistence changes plus migration updates
- Frontend work will need to reflect auto-paused one-time alerts and clarify resumed/re-armed behavior
- Notification records and scheduler behavior must preserve distinct recurring occurrences without collapsing them into one per day
- Market-data runtime behavior will prefer fresher reusable snapshots at the cost of a shorter stale-serving window during upstream incidents
