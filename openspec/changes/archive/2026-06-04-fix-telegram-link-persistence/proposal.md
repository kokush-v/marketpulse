## Summary

Fix Telegram bot linking so a successful `/start` linking flow persists the active Telegram connection for subsequent bot interactions.

## Problem

The current Telegram linking flow can report a successful link from the bot while failing to persist the active connection for later requests. In practice, a user can receive a successful linking message and then immediately see a safe not-linked outcome when opening `Profile`.

## Proposed Solution

Tighten the Telegram linking implementation so a successful bot linking flow durably saves the active Telegram connection before the bot returns a success outcome.

## Scope

- Telegram bot linking persistence after a successful `/start` flow
- Backend transaction handling for the Telegram link activation path
- Focused backend regression coverage for link persistence across subsequent bot requests

## Non-Goals

- Changing the web-side Telegram connection UX
- Changing bot-side profile content or unlink UX
- Changing Telegram notification delivery behavior

## Impact

This change restores the approved Telegram behavior where a completed bot linking flow leaves the Telegram account actively linked for later profile and notification flows.
