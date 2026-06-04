## Summary

Add scheduled alert evaluation so MarketPulse checks all user alert types every five minutes, catches up missed evaluation windows after downtime, records notification history for triggered alerts, and delivers triggered alerts to linked Telegram accounts through background execution.

## Problem

MarketPulse already lets authenticated users create and manage alerts, and it already defines Telegram delivery behavior once an alert becomes eligible to trigger. However, the current approved specs do not define how alert eligibility is evaluated on a schedule, how frequently checks run, or what happens when scheduled execution is interrupted.

Without an explicit scheduled evaluation contract, implementation would risk:

- inconsistent trigger timing across alert types
- unclear behavior after worker restarts or deployment downtime
- missing or duplicated notifications when evaluation windows are skipped
- tight coupling to one infrastructure choice before product behavior is approved

## Proposed Solution

Introduce a focused change that defines scheduled background evaluation for all supported alert types. The system will evaluate eligible alerts every five minutes, determine trigger eligibility according to each alert's existing rules and time behavior, record notification history for triggered alerts, and deliver triggered alerts to Telegram when the user has an active Telegram connection.

The change will also define catch-up behavior after downtime so missed evaluation windows are processed in order rather than silently skipped.

## Scope

- scheduled evaluation for all supported alert types: `Price above`, `Price below`, and `News`
- a five-minute evaluation cadence for alert processing
- catch-up processing for missed evaluation windows after scheduler or worker downtime
- notification-history creation for triggered alerts
- Telegram delivery for triggered alerts when the user has an active Telegram connection
- background-job observability for evaluation and delivery failures
- design guidance for an implementation-flexible background execution model

## Non-Goals

- adding new alert types or changing alert authoring UX
- adding user-configurable alert schedules or per-alert cadence settings
- adding quiet hours, digest batching, or advanced notification preferences
- defining new frontend screens beyond behavior already needed to surface resulting notification history
- locking the implementation to a single scheduler or queue technology

## Impact

Affected domains:

- `alerts`
- `background-jobs`
- `notifications`

Primary workflows:

- authenticated user receives Telegram delivery after an alert becomes eligible during scheduled evaluation
- authenticated user still receives missed eligible alert processing after temporary scheduler downtime
- operators can observe evaluation and delivery failures without losing prior alert state

This change establishes the missing runtime contract between saved alert definitions and actual scheduled notification delivery, while preserving flexibility for the final infrastructure implementation choice.
