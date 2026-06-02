## Context

This change extends the approved Telegram integration behavior in two narrow areas:

1. bot-side self-service profile inspection and unlinking
2. Telegram-chat replacement behavior for repeated test notifications

The change stays within existing Telegram linking and notification domains and does not introduce new product roles or broader notification-policy changes.

## Goals

- Let a linked Telegram user inspect which MarketPulse profile is currently connected without leaving the bot.
- Let a linked Telegram user unlink from the bot through an explicit confirmation flow.
- Keep Telegram test notifications tidy by replacing the previous test message in chat when possible.
- Preserve notification-history retention even when Telegram chat cleanup occurs.

## Non-Goals

- Changing link creation, deep-link generation, or token issuance rules.
- Changing alert or digest delivery behavior for non-test notifications.
- Removing historical notification records from the application database.
- Introducing account edits or profile-management features beyond inspect and unlink.

## Bot Interaction Design

### Profile entry point

The bot exposes a `Profile` action for users who interact with the Telegram integration. When the current Telegram account is actively linked to a MarketPulse user, the profile view presents:

- profile avatar
- profile email
- profile display name

The profile message includes a reply-button action for `Unlink Profile`.

When the Telegram account is not actively linked, the profile flow should return a safe not-linked outcome rather than exposing another user's data or failing with raw provider errors.

### Unlink confirmation

`Unlink Profile` is a destructive integration-management action, so the bot must require explicit confirmation before applying it. If the user confirms:

- the active Telegram link is deactivated
- future Telegram deliveries for that link stop until a new link is created

If the user cancels or abandons the flow:

- the existing link remains unchanged

## Test Notification Replacement

Test notification replacement applies only to Telegram test notifications. It does not apply to normal alert notifications or future digest notifications.

Before sending a new test notification to a linked user, the system attempts to delete the previously tracked Telegram test-notification message for that same linked user in the Telegram chat. This behavior is chat cleanup only.

Persistent notification records remain intact. The system does not delete prior notification-history rows from the database as part of test-message replacement.

If deletion of the previous Telegram test message fails because the message is already gone, is no longer deletable, or Telegram returns another safe upstream failure:

- the system still sends the new test notification
- the failure is handled as a non-blocking cleanup issue

- Bot-side profile data must correspond only to the MarketPulse user actively linked to the current Telegram account.
- Unlink actions must affect only the active link for the current Telegram account.
- The bot must not expose profile details for inactive, superseded, or unrelated links.
- Safe outcomes should be returned when no active link exists or when Telegram-side cleanup fails.

## External Integration Considerations

This change depends on Telegram Bot API behavior for:

- sending profile and confirmation messages
- rendering reply-button actions
- deleting previously sent bot messages when test-message replacement is attempted

Deletion support is not guaranteed for every prior message state, so the contract intentionally treats deletion failure as non-blocking.

## Testing Considerations

Implementation should verify:

- linked user sees avatar, email, and display name in the bot profile flow
- unlink requires confirmation
- confirmed unlink deactivates the current link
- cancelled unlink preserves the link
- a new test notification deletes the previous tracked test message when Telegram allows deletion
- a new test notification still sends when prior-message deletion fails
- notification-history records remain preserved during test-message replacement
