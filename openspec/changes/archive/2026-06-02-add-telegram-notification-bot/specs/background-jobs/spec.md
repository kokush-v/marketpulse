## MODIFIED Requirements

### Requirement: Refresh Public Market Overview Snapshots Outside the Request Path
The system SHALL support a background execution path that refreshes reusable public market overview snapshots for production deployments of the Ruby market-data service and dispatches Telegram alert notifications outside user-facing request-response flows.

#### Scenario: Scheduled refresh updates the reusable snapshot
- **Given** a production deployment has background refresh configured for the Ruby market-data service
- **When** the scheduled refresh runs successfully
- **Then** the system updates the reusable public market overview snapshot without requiring a public dashboard request to rebuild it

#### Scenario: Refresh failure preserves the last successful snapshot
- **Given** the Ruby market-data service has an existing successful reusable market overview snapshot
- **When** a background refresh fails because of provider outage, malformed data, timeout, or rate limit
- **Then** the system SHALL preserve the last successful snapshot according to the documented retention policy
- **And** the failure SHALL be observable through logs or metrics

#### Scenario: Alert trigger dispatches Telegram notification asynchronously
- **Given** an authenticated user has an active Telegram link
- **And** one of the user's alerts becomes eligible to trigger
- **When** the system prepares Telegram delivery for that alert
- **Then** the Telegram send attempt runs through background execution rather than blocking a user-facing request

#### Scenario: Telegram background delivery fails
- **Given** an authenticated user has an active Telegram link
- **And** one of the user's alerts becomes eligible to trigger
- **When** the background Telegram delivery attempt fails
- **Then** the failure SHALL be observable through logs, metrics, or recorded notification status
