## Overview

This change introduces Telegram account linking and Telegram alert notification delivery for authenticated MarketPulse users. The design keeps the web product as the source of truth for user ownership and uses the Telegram bot only as a controlled confirmation and delivery surface.

The design follows three principles:
- linking starts from an authenticated web session, not from Telegram alone
- one Telegram account can be actively linked to only one MarketPulse user at a time
- alert delivery runs outside user-facing request-response paths

## User Flows

### Connect Telegram

1. The authenticated user opens the protected dashboard `Integrations` workspace.
2. The user starts Telegram connection from the `Telegram` card.
3. The backend creates a short-lived, one-time linking token for that user.
4. The frontend shows:
   - an `Open bot` deep link that includes the token in the Telegram `start` parameter
   - a copyable fallback code for manual use if needed
5. The user opens the bot and starts the linking flow.
6. The bot validates the token and links the Telegram account to the originating MarketPulse user.
7. The product shows the Telegram integration as connected.

### Change Account

1. A Telegram account that is already linked uses the bot's `Change account` action.
2. The bot does not silently switch ownership.
3. The bot asks for explicit confirmation before allowing a switch.
4. The user signs into the desired MarketPulse web account and starts a new Telegram connect flow there.
5. The new token is consumed only after confirmation and only for the newly authenticated web account.
6. The previous active link is deactivated and the new link becomes active.

### Disconnect

1. The authenticated user disconnects Telegram from the web product.
2. The active Telegram link is deactivated.
3. Future alert notifications to Telegram stop for that user unless a new link is established.

### Alert Notification Delivery

1. An alert becomes eligible to trigger for a user.
2. Background execution evaluates delivery eligibility for configured channels.
3. If the user has an active Telegram connection, the system sends an alert message to the linked Telegram chat.
4. The system records whether delivery succeeded or failed with a frontend-safe status.

## Data Model

### Telegram Connections

Add a table for active and historical Telegram account links. Expected fields include:
- local user reference
- Telegram user identifier
- Telegram chat identifier
- optional Telegram username
- status
- connected timestamp
- disconnected timestamp

This table supports one active Telegram link per local user and one active local user per Telegram account.

### Telegram Connection Tokens

Add a table for one-time linking tokens. Expected fields include:
- local user reference
- token hash
- created timestamp
- expiration timestamp
- used timestamp
- revoked timestamp

Raw tokens should not be stored after issuance. The system should compare hashed values when consuming a token.

### Notifications

Add or extend notification persistence so Telegram alert delivery outcomes can be observed. Expected tracked fields include:
- local user reference
- notification type
- channel
- delivery status
- status timestamps
- message summary or payload reference

The design does not require a separate bot session table for V1.

## Ownership and Security

- Telegram linking SHALL always originate from an authenticated MarketPulse user context.
- Linking tokens SHALL be short-lived and one-time-use.
- Linking tokens SHALL be invalid after expiration, successful use, revocation, or disconnect-driven invalidation.
- The system SHALL prevent one Telegram account from remaining actively linked to multiple MarketPulse users at the same time.
- Account switching SHALL require explicit confirmation and SHALL NOT silently transfer a Telegram account to another user.
- The frontend and bot responses SHALL return safe conflict or expiry outcomes without exposing internal identifiers or secrets.

## External Integration Notes

- The Telegram bot is used for account linking confirmation and message delivery.
- The primary product remains responsible for ownership decisions and token issuance.
- The bot should support the initial `/start` flow and an explicit `Change account` action in V1.
- Deep links should be the primary connect path, while copyable code remains a fallback path.

## Background Execution

Telegram alert delivery should not block user-facing requests. The system should dispatch eligible Telegram alert notifications through background execution after the alert trigger is determined.

This change does not require daily digest scheduling or advanced retry orchestration, but it does require observable success and failure outcomes for Telegram delivery.

## API and Frontend Contract Notes

The protected frontend needs integration-management API support for:
- reading Telegram connection state
- initiating Telegram connect and receiving a fresh linking token plus bot deep link
- disconnecting Telegram

If these endpoints are added or changed in implementation, Orval-generated frontend clients must be regenerated as part of that implementation change.

## Risks and Rollback

Primary risks:
- stale or replayed linking tokens
- incorrect ownership transfer during account switching
- failed Telegram delivery producing inconsistent user-facing state

Rollback approach:
- disable Telegram connect initiation in the UI
- stop background Telegram delivery
- preserve existing notification and link records for auditability while preventing new linking or sends
