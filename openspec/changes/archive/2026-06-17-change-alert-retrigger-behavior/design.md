## Overview

This change upgrades alert runtime behavior without expanding alert authoring into new product areas. The goal is to make consumed one-time alerts clearly visible, let resumed one-time alerts start from a fresh baseline, let recurring alerts produce multiple meaningful same-day notifications when distinct market or news events occur, split scheduler responsibilities by alert family, and keep market-overview-backed alert context fresher.

## Goals

- Make fired one-time alerts visibly paused in the product.
- Re-arm resumed one-time alerts from current state instead of stale baseline state.
- Let recurring price alerts trigger more than once in the same day when each new trigger is based on a newly established baseline.
- Let recurring news alerts notify on distinct newly available articles even when several arrive on the same day.
- Preserve catch-up safety and notification-history visibility for distinct recurring occurrences.
- Separate price-alert and news-alert scheduling so each family can evolve independently.
- Reduce market-overview snapshot freshness and stale retention windows for timelier alert-adjacent context.

## Non-Goals

- Adding new alert types.
- Adding per-alert user-configurable cooldown controls.
- Changing cron cadence or broader Telegram account behavior.
- Changing asset-search or news caching policy.

## Lifecycle Model

### One-time alerts

One-time alerts remain user-authored as a separate timing mode, but after a successful trigger they no longer stay visibly active. The system should transition them into the existing paused lifecycle so the UI and protected APIs show that the alert has been consumed.

When a user later resumes such an alert, the alert should not reuse the historical trigger baseline that caused the earlier notification. Resume should re-arm the alert from current state:

- price alerts derive a fresh baseline from the current market price at resume time when percentage-based logic needs one
- news alerts derive a fresh news baseline from the newest visible article state at resume time so older already-seen articles do not re-trigger

### Recurring alerts

Recurring alerts continue to use the same date-window concept, but they should no longer be limited to one trigger per calendar day. Instead, recurrence means the alert stays eligible throughout its configured active date range and may trigger again after it has been successfully re-armed.

For price alerts, each successful recurring trigger should establish the next trigger baseline from the current price at trigger time. This lets later same-day market moves create new meaningful trigger opportunities rather than repeatedly comparing against the original stale baseline.

For news alerts, each successful recurring trigger should advance article-tracking state so later newly published articles remain eligible to create separate notifications.

## Persistence And Data Model Notes

The current persistence shape stores only a coarse `last_triggered_on` day-level marker, which is insufficient for the new behavior. Implementation should introduce durable state that can represent:

- whether a one-time alert has already consumed its current arm and therefore must show paused
- the current active baseline for percentage-based price triggers
- the current news baseline for detecting only unseen newer articles
- distinct recurring trigger occurrences inside the same calendar day
- catch-up-safe deduplication that prevents replaying the same occurrence twice while still allowing later legitimate same-day occurrences

The exact schema is implementation-defined, but a migration is expected because the current day-level trigger marker cannot express the new recurring semantics by itself.

## Background Evaluation

The scheduler cadence stays at five minutes. What changes is how recurring triggers are identified:

- a recurring alert that triggered earlier the same day may become eligible again after its state is re-armed
- catch-up processing must preserve ordering of missed windows so recurring price/news baselines advance consistently
- deduplication must be occurrence-based rather than day-based for recurring alerts

This means event identity can no longer be derived only from `{alert_id, calendar_day}` for recurring alerts.

## Scheduler Architecture

The prior shared alert scheduler mixed:

- due-window processing
- cursor advancement
- scenario branching
- trigger dispatch
- runtime-state persistence

This change separates those responsibilities by alert family while keeping shared orchestration centralized. The runtime should use:

- separate price-alert and news-alert scheduled jobs
- separate persisted cursors for price and news catch-up progress
- a shared creator-style orchestration layer for dispatch, logging, and persistence
- concrete creators that produce scenario-family evaluators through a Factory Method

This keeps price and news alert logic independently evolvable without duplicating the full orchestration path.

## Market Overview Freshness

Alert-adjacent selected-coin context depends on reusable market overview snapshots. The previous one-hour fresh window and six-hour stale fallback window are too permissive for crypto tracking workflows that expect faster movement.

This change reduces:

- fresh snapshot lifetime from one hour to fifteen minutes
- stale fallback retention from six hours to thirty minutes

The refresh cadence, lock behavior, and overall reusable snapshot design stay unchanged. The tradeoff is intentionally biased toward fresher context rather than longer stale-serving resilience.

## API And Frontend Impact

Protected alert APIs and the dashboard UI must reflect:

- a fired one-time alert now appears paused after its successful trigger
- resuming a fired one-time alert creates a fresh armed state
- recurring alerts remain active after trigger and may notify again later in the same date window
- the backend cron/runtime architecture now separates price and news alert evaluation jobs, although product API behavior remains stable

If existing response fields are not enough to explain resumed versus consumed behavior clearly, the implementation may extend the protected alert response contract and regenerate Orval clients in the same implementation change.

## Notification History

Notification history should continue to be user-scoped and observable, but recurring notifications must remain distinct when multiple legitimate trigger occurrences happen on the same day. The system should record separate history entries for separate recurring occurrences instead of collapsing all same-day recurring activity into one record.

## Risks

- Re-arming recurring price alerts incorrectly could create noisy repeated notifications during sideways market movement.
- News recurrence needs clear article-progress tracking so catch-up runs do not resend already-recorded articles.
- UI wording must make paused one-time alerts and resumed alerts understandable without implying deletion or permanent completion.
- Split scheduler deployment requires operators to rebuild the cron container so the new registrations replace the previous single-job runtime.
- Shorter market-overview stale retention reduces outage cushion during prolonged upstream issues.

## Rollback

If this change must be rolled back, rollback should restore the earlier once-per-day recurring semantics and remove any new persistence introduced for re-arming or occurrence-level deduplication, while preserving existing user-owned alerts and notification history where possible.
