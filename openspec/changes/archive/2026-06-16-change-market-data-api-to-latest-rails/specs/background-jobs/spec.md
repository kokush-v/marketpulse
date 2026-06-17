## MODIFIED Requirements

### Requirement: Refresh Public Market Overview Snapshots Outside the Request Path
The system SHALL support a background execution path that refreshes reusable public market overview snapshots for production deployments of the Ruby market-data service and dispatches Telegram alert notifications outside user-facing request-response flows, and SHALL preserve snapshot-refresh behavior and observability through approved runtime upgrades of the Ruby service.

#### Scenario: Scheduled refresh updates the reusable snapshot after runtime upgrade
- **Given** a production deployment has background refresh configured for the Ruby market-data service
- **And** the Ruby service runtime has been upgraded
- **When** the scheduled refresh runs successfully
- **Then** the system updates the reusable public market overview snapshot without requiring a public dashboard request to rebuild it

#### Scenario: Refresh failure remains observable after runtime upgrade
- **Given** the upgraded Ruby market-data service has an existing successful reusable market overview snapshot
- **When** a background refresh fails because of provider outage, malformed data, timeout, or rate limit
- **Then** the system SHALL preserve the last successful snapshot according to the documented retention policy
- **And** the failure SHALL remain observable through logs or metrics
