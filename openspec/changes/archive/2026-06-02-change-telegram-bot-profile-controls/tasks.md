## 1. Spec Updates

- [x] 1.1 Update the `telegram` domain contract to define bot-side profile viewing with avatar, email, and display name for the actively linked user.
- [x] 1.2 Update the `telegram` domain contract to define a bot-side `Unlink Profile` reply action with explicit confirmation behavior and safe outcomes when no active link exists.
- [x] 1.3 Update the `notifications` domain contract to define Telegram test notification replacement behavior that attempts to delete the previously sent test message in chat before sending a new one.
- [x] 1.4 Update the `notifications` domain contract to define fallback behavior where a failed Telegram delete attempt does not block the new test notification send and does not require deleting notification-history records from the database.

## 2. Design

- [x] 2.1 Document the Telegram bot interaction design for `Profile`, `Unlink Profile`, confirmation, and test-message replacement tracking.
- [x] 2.2 Document ownership, Telegram API failure handling, and the distinction between Telegram chat cleanup and persistent notification-history retention.

## 3. Validation

- [x] 3.1 Run `openspec validate change-telegram-bot-profile-controls --strict`.
