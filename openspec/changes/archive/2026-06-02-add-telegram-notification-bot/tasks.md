## 1. OpenSpec
- [x] 1.1 Add `telegram` requirements for dashboard integration state, connection, relinking, and disconnect behavior
- [x] 1.2 Add `notifications` requirements for Telegram alert delivery history and safe delivery outcomes
- [x] 1.3 Modify `background-jobs` requirements to cover asynchronous Telegram notification dispatch for alert triggers
- [x] 1.4 Modify `alerts` requirements to state that eligible alert triggers can deliver to a connected Telegram account
- [x] 1.5 Document architecture, token lifecycle, ownership rules, and persistence in `design.md`

## 2. Backend
- [x] 2.1 Add persistence for Telegram connections and one-time Telegram connection tokens
- [x] 2.2 Add protected backend endpoints for integrations state, Telegram connect initiation, and Telegram disconnect
- [x] 2.3 Add Telegram bot webhook or polling handling for `/start` linking and `Change account` confirmation flow
- [x] 2.4 Add backend notification dispatch behavior that delivers eligible alert notifications to linked Telegram chats
- [x] 2.5 Add backend-safe validation and conflict handling for expired, used, revoked, or cross-account tokens

## 3. Database
- [x] 3.1 Add migrations for Telegram connection and connection-token tables
- [x] 3.2 Add migrations for notification records needed to track Telegram delivery status and timestamps
- [x] 3.3 Enforce single-active-link ownership constraints for Telegram account linkage

## 4. Frontend
- [x] 4.1 Add a protected `Integrations` dashboard workspace with a Telegram integration card
- [x] 4.2 Add Telegram connect UI states for not connected, token ready, connected, and error
- [x] 4.3 Add `Open bot`, `Copy code`, and disconnect user flows in the Telegram card
- [x] 4.4 Regenerate Orval client artifacts if API contracts change

## 5. Integrations
- [x] 5.1 Configure Telegram bot integration behavior and environment settings required for linking and alert delivery
- [x] 5.2 Ensure bot responses support initial linking success, already-linked conflict handling, and account-switch confirmation

## 6. Tests and Validation
- [x] 6.1 Add backend tests for Telegram token issuance, expiry, consumption, and ownership enforcement
- [x] 6.2 Add backend tests for connect, disconnect, and change-account flows
- [x] 6.3 Add backend or integration tests for Telegram alert notification delivery outcomes
- [x] 6.4 Validate the OpenSpec change with `openspec validate add-telegram-notification-bot --strict`
