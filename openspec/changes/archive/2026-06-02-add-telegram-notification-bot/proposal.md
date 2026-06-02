## Summary

Add a Telegram notification bot integration that allows authenticated users to connect a personal Telegram account from a new dashboard `Integrations` workspace, safely switch the linked MarketPulse account when needed, and receive alert notifications through Telegram.

## Problem

MarketPulse MVP already includes alerts and Telegram notifications in product scope, but the current specs do not define how a user links a Telegram account, manages that connection from the product, or receives alert notifications through a bot. Without this change, the alerting experience stops at in-app configuration and cannot deliver notifications to Telegram.

## Proposed Solution

Introduce a focused Telegram integration flow centered on a dashboard `Integrations` workspace and a `Telegram` card. When a user starts the connection flow, the system issues a short-lived one-time linking token and presents a deep link to the Telegram bot using the token as the `start` parameter. The product also shows a copyable fallback code. The bot uses the token to connect the Telegram account to the authenticated MarketPulse user.

The bot also supports a controlled `Change account` flow so one Telegram account can be re-linked to another MarketPulse user only after explicit confirmation. The web product supports disconnecting Telegram from the current user. Once connected, the system can deliver alert notifications to the linked Telegram chat and record delivery outcomes.

## Scope

Affected domains:
- `telegram`
- `notifications`
- `background-jobs`
- `alerts`

Primary user workflows:
- view Telegram connection state in dashboard integrations
- start Telegram connection from the web app
- complete Telegram linking through the bot
- safely switch the linked MarketPulse account from Telegram
- disconnect Telegram from the web app
- receive alert notifications through Telegram after alert triggers

Included in this change:
- dashboard `Integrations` workspace behavior for Telegram connection management
- Telegram bot linking through deep link and fallback copyable token
- one-time short-lived token lifecycle for Telegram linking
- single-active-link ownership rules for Telegram accounts
- `Change account` flow in the bot with explicit confirmation
- web disconnect flow
- Telegram alert notification delivery and delivery history/status
- background execution requirements needed to dispatch Telegram notifications outside request-response flows

## Non-Goals

- daily digest delivery
- Telegram-based sign-in to MarketPulse
- managing alerts from Telegram
- Telegram group or channel delivery
- multilingual bot behavior
- quiet hours, timezone preferences, or advanced notification preferences
- advanced retry orchestration beyond safe delivery-state recording

## Impact

This change introduces a new Telegram integration capability, new persistence for Telegram linking tokens and active connections, and notification delivery tracking for Telegram alert messages. It also adds a new protected dashboard area for integration management and requires background job behavior for asynchronous notification dispatch. Because this change adds external integration behavior, user ownership rules, and persistence, it requires a design document and follow-up implementation work across backend, frontend, database, and integration layers.
