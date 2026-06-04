## Overview

This change defines scheduled alert evaluation as a backend-owned background capability. Saved alerts already model user intent and Telegram delivery already has an approved downstream contract, but the system still needs a stable execution contract that explains when evaluation runs, how missed runs are recovered, and how duplicate notifications are avoided.

The design intentionally describes observable behavior and architectural constraints without forcing one queue or scheduler product. This keeps the OpenSpec change compatible with a Celery-based implementation, another worker framework, or an external scheduler that triggers backend-owned evaluation work.

## Goals

- Evaluate all supported alert types on a predictable five-minute cadence.
- Recover missed evaluation windows after downtime instead of silently skipping them.
- Produce notification-history records for triggered alerts.
- Deliver triggered alerts to Telegram asynchronously for linked users.
- Keep evaluation and delivery idempotent enough to avoid duplicate user-visible notifications during retries or catch-up.

## Non-Goals

- Redesign alert rule semantics.
- Introduce user-customizable schedules.
- Define digest batching or quiet-hour behavior.
- Require a specific queueing or scheduler product in the approved contract.

## Evaluation Model

The system evaluates alerts in discrete five-minute windows. Each run determines which alerts are eligible for evaluation in that window based on:

- alert status such as active versus paused
- alert time behavior such as one-time or daily recurring
- recurring alert date boundaries
- per-alert rule semantics for `Price above`, `Price below`, and `News`

When a run finds a trigger:

1. the alert trigger is recorded in notification history
2. Telegram delivery is attempted only if the user has an active Telegram connection
3. delivery outcome remains observable even if Telegram sending fails

Users without Telegram connections still have valid alert triggers. Their triggers should be recorded according to the approved notifications contract even when no Telegram send occurs.

## Catch-Up Model

The system must not silently skip missed five-minute windows caused by process downtime, deployment gaps, or delayed workers. Instead, the next available background execution resumes from the oldest unprocessed evaluation window and works forward in order until the system catches up to the current schedule.

Catch-up behavior should preserve product semantics:

- one-time alerts should not notify more than once for the same qualifying event window
- daily recurring alerts should still trigger at most once per calendar day
- catch-up processing should not generate duplicate notification-history records or duplicate Telegram sends for the same alert occurrence

The exact persistence model is implementation-defined, but the implementation will likely need durable progress tracking for evaluation windows and per-alert trigger bookkeeping.

## Idempotency And Failure Handling

Scheduled evaluation and Telegram delivery are both retry-prone operations. The implementation should support idempotent reprocessing so a retried run or partially failed catch-up sequence does not create duplicate user-visible outcomes.

Expected safety properties:

- a failed evaluation window may be retried
- a failed Telegram send may be retried according to the delivery strategy
- duplicate notification history for the same alert occurrence should be prevented
- duplicate Telegram sends for the same alert occurrence should be prevented where practical

Failures should remain observable through logs, metrics, job records, or persisted notification status. Failure handling should not require mutating alert ownership or alert definitions.

## Ownership And Security

All evaluation remains backend-owned and must continue to enforce user ownership from stored alert records and linked Telegram state. The scheduler or worker must never rely on client-supplied user identifiers for ownership decisions.

Any background worker that reads alerts or sends Telegram messages must:

- use backend-managed credentials only
- resolve the target user and linked Telegram chat from trusted persisted data
- preserve row ownership guarantees in alert and notification queries

## Architecture Guidance

This OpenSpec change does not require one exact infrastructure stack, but the implementation should preserve these boundaries:

- scheduling is separated from HTTP request-response handling
- evaluation work runs in background execution
- Telegram delivery runs in background execution
- scheduler state and trigger bookkeeping are durable enough to support catch-up

A Celery-based design is a reasonable implementation option if the team wants a dedicated scheduler plus workers, but it is not required by this spec. An external cron that triggers backend-owned evaluation jobs or another async worker system can also satisfy the contract as long as five-minute cadence, catch-up behavior, and idempotent outcomes are preserved.

## Risks

- Catch-up can create burst load after long downtime.
- News alerts may require careful deduplication when many articles arrive between runs.
- Price-based alerts may need stable market-data sourcing rules to avoid inconsistent catch-up results across windows.
- Duplicate sends become more likely if evaluation progress is not persisted durably.

## Rollback

If implementation needs to be rolled back later, rollback should remove the scheduled evaluation path and any new persistence used for evaluation progress or deduplication, while leaving existing alert-management behavior intact.
