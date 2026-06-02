## Summary

Refine the Telegram integration experience by adding bot-side profile management controls and by making test notification delivery replace the previously sent test message in the user's Telegram chat.

## Problem

The current Telegram integration contract centers on web-initiated linking and web-side disconnect actions, but it does not define how a linked user can inspect the currently connected MarketPulse profile or unlink directly from inside the Telegram bot. That leaves the bot without a clear self-service profile-management flow.

The current notification contract also does not define dedicated behavior for test notifications. Without an explicit replacement rule, repeated test sends can clutter the user's Telegram chat with stale test messages and make the test flow feel noisy.

## Proposed Solution

Extend the Telegram domain to define a bot-side `Profile` entry point that shows the linked MarketPulse profile details, including avatar, email, and display name, and exposes an `Unlink Profile` reply action beneath that profile message.

Add a confirmed bot-side unlink flow so users can disconnect their Telegram link directly from the bot without using the web integrations screen.

Extend the notifications domain to define test notification replacement behavior in Telegram chats. Before sending a new test notification, the system should attempt to delete the previously tracked test-notification message for that linked user in Telegram chat history. If deletion fails, the system should still send the new test notification and should not require database history deletion as part of that replacement behavior.

## Scope

Affected domains:

- `telegram`
- `notifications`

Primary user workflows:

- a linked user opens the Telegram bot profile view and sees the linked MarketPulse avatar, email, and display name
- a linked user chooses `Unlink Profile` from the bot and confirms the unlink action
- a linked user requests a test notification and sees the newest test message replace the prior one in chat when deletion is possible
- a linked user still receives a new test notification when prior test-message deletion fails

In scope:

- bot-side profile viewing for an actively linked Telegram user
- reply-button access to `Unlink Profile` from the profile message
- confirmation behavior before unlinking from the bot
- bot-side unlink behavior that deactivates the current Telegram link
- Telegram-chat replacement behavior for test notifications only
- tolerant handling when deletion of the previous Telegram test message fails
- preserving notification records rather than deleting database history during test-message replacement

## Non-Goals

- changing the existing web-side Telegram linking flow
- changing production alert-notification or digest-notification history retention rules
- deleting historical notification records from the database
- deduplicating or collapsing non-test alert notifications
- redesigning general Telegram bot navigation beyond the profile and unlink actions required for this change

## Impact

This change makes the Telegram bot feel more complete as a self-service integration surface and keeps repeated test sends tidy in chat without changing notification-history retention. It also introduces explicit behavioral expectations for bot-side unlink confirmation and graceful degradation when Telegram message deletion is unavailable.
