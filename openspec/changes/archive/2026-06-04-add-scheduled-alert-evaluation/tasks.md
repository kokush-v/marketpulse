- [x] 1.1 Add `background-jobs` requirements for five-minute alert evaluation, catch-up behavior, and observable failure handling.
- [x] 1.2 Modify `alerts` requirements to define scheduled eligibility evaluation for all supported alert types and safe handling for users without Telegram links.
- [x] 1.3 Modify `notifications` requirements to define notification-history creation for scheduled alert triggers and delivery outcomes during catch-up runs.
- [x] 1.4 Add a design document that covers evaluation cadence, catch-up strategy, idempotency, ownership boundaries, and implementation-flexible worker architecture.
- [x] 1.5 Validate the OpenSpec change with `openspec validate add-scheduled-alert-evaluation --strict`.

- [x] 2.1 Implement backend background execution for scheduled alert evaluation every five minutes.
- [x] 2.2 Implement catch-up processing that evaluates missed alert windows in order after downtime or delayed execution.
- [x] 2.3 Implement alert evaluation across all supported alert types using existing alert ownership and time-behavior rules.
- [x] 2.4 Create notification-history records for each triggered alert evaluation outcome required by the approved contract.
- [x] 2.5 Deliver triggered alerts to linked Telegram chats through background execution without blocking user-facing requests.
- [x] 2.6 Add or update persistence needed to track evaluation progress, catch-up state, idempotency, or delivery status.

- [x] 3.1 Add backend or integration tests for five-minute scheduled evaluation across `Price above`, `Price below`, and `News` alerts.
- [x] 3.2 Add backend or integration tests for recurring-alert once-per-day limits during normal runs and catch-up runs.
- [x] 3.3 Add backend or integration tests for catch-up behavior after missed runs, including no-skip and no-duplicate expectations.
- [x] 3.4 Add backend or integration tests for notification-history creation and Telegram delivery outcomes for linked and unlinked users.
- [x] 3.5 Validate the OpenSpec change with `openspec validate add-scheduled-alert-evaluation --strict`.
