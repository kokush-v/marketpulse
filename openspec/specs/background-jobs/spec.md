# background-jobs Specification

## Purpose
TBD - created by archiving change improve-market-data-service-concurrency. Update Purpose after archive.
## Requirements
### Requirement: Refresh Public Market Overview Snapshots Outside the Request Path
The system SHALL support a background execution path that refreshes reusable public market overview snapshots for production deployments of the Ruby market-data service.

#### Scenario: Scheduled refresh updates the reusable snapshot
- **Given** a production deployment has background refresh configured for the Ruby market-data service
- **When** the scheduled refresh runs successfully
- **Then** the system updates the reusable public market overview snapshot without requiring a public dashboard request to rebuild it

#### Scenario: Refresh failure preserves the last successful snapshot
- **Given** the Ruby market-data service has an existing successful reusable market overview snapshot
- **When** a background refresh fails because of provider outage, malformed data, timeout, or rate limit
- **Then** the system SHALL preserve the last successful snapshot according to the documented retention policy
- **And** the failure SHALL be observable through logs or metrics

