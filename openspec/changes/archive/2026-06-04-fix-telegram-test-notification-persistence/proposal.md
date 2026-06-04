## Summary

Fix Telegram test notification persistence so a successful test send updates the tracked last test message identifier and records the latest test notification attempt for cooldown enforcement.

## Problem

The current Telegram test notification flow can successfully send a Telegram message while failing to persist the database updates that should follow the send. In practice, the latest test message identifier may remain unset and the latest test notification record may not be durably saved, which breaks previous-message cleanup and per-user cooldown behavior.

## Proposed Solution

Tighten the Telegram test notification backend flow so a successful send durably persists the resulting `last_test_message_id` and notification delivery record before the request completes.

## Scope

- Backend persistence behavior for successful Telegram test notification sends
- Focused regression coverage for tracked test message updates and cooldown persistence after a send

## Non-Goals

- Changing Telegram bot linking behavior
- Changing alert notification delivery behavior outside the test notification flow
- Redesigning Telegram integration UI or bot UX

## Impact

This change restores the approved Telegram test notification behavior where the system can delete the previous test message on the next send and enforce the per-user cooldown based on the most recent persisted test attempt.
