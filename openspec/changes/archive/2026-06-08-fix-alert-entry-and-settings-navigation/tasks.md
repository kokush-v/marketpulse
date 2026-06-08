## 1. Watchlist saved-coins behavior

- [x] 1.1 Update the watchlist workspace so the saved-coins list uses an internal scroll region when saved assets exceed the available panel height.
- [x] 1.2 Replace the watchlist `Add alert` placeholder behavior with navigation to the create-alert flow while preserving the selected watchlist asset context.

## 2. Alert creation entry behavior

- [x] 2.1 Update the standard `New alert` flow so opening `/alerts/new` does not automatically preselect the first watchlist coin.
- [x] 2.2 Support contextual alert creation from watchlist assets so the chosen coin is preselected only for that entry path.
- [x] 2.3 Keep the create-alert stepper on the coin-selection step when a contextual preselected coin is provided.

## 3. Settings and integrations navigation

- [x] 3.1 Move Telegram integration management from the standalone `Integrations` workspace into the protected dashboard `Settings` workspace.
- [x] 3.2 Redirect the legacy `Integrations` route to the dashboard `Settings` workspace.
- [x] 3.3 Remove unused dashboard sidebar tabs covered by this change, including the standalone `Integrations` entry and the duplicate sidebar `Settings` entry when avatar-menu settings navigation remains available.

## 4. Validation

- [x] 4.1 Run `openspec validate fix-alert-entry-and-settings-navigation --strict`.
- [x] 4.2 Run relevant frontend checks for the touched navigation and alert/watchlist flows using the project's existing scripts.
