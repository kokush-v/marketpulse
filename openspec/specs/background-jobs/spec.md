# background-jobs Specification

## Purpose
Define the background execution behavior used to refresh reusable snapshots and other off-request product work without blocking user-facing requests.
## Requirements
### Requirement: Refresh Public Market Overview Snapshots Outside the Request Path
The system SHALL support a background execution path that refreshes reusable public market overview snapshots for production deployments of the Ruby market-data service and dispatches Telegram alert notifications outside user-facing request-response flows.

#### Scenario: Scheduled refresh updates the reusable snapshot
- **Given** a production deployment has background refresh configured for the Ruby market-data service
- **When** the scheduled refresh runs successfully
- **Then** the system updates the reusable public market overview snapshot without requiring a public dashboard request to rebuild it
- **And** the documented fresh snapshot window SHALL not exceed fifteen minutes after that successful refresh

#### Scenario: Refresh failure preserves the last successful snapshot
- **Given** the Ruby market-data service has an existing successful reusable market overview snapshot
- **When** a background refresh fails because of provider outage, malformed data, timeout, or rate limit
- **Then** the system SHALL preserve the last successful snapshot according to the documented retention policy
- **And** that stale fallback retention policy SHALL not exceed thirty minutes after the last successful snapshot
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

### Requirement: Evaluate Alerts Every Five Minutes Outside User Requests
The system SHALL run alert evaluation through background execution on a five-minute cadence rather than during user-facing request-response flows, and SHALL schedule price-alert evaluation separately from news-alert evaluation.

#### Scenario: Scheduled price-alert evaluation runs on cadence
- **Given** production background execution is configured for alerts
- **When** the next five-minute price-alert evaluation window arrives
- **Then** the system evaluates eligible price alerts in background execution without requiring a user-facing request

#### Scenario: Scheduled news-alert evaluation runs on cadence
- **Given** production background execution is configured for alerts
- **When** the next five-minute news-alert evaluation window arrives
- **Then** the system evaluates eligible news alerts in background execution without requiring a user-facing request

#### Scenario: Evaluation failure remains observable
- **Given** production background execution is configured for alert evaluation jobs
- **When** a scheduled price-alert or news-alert run fails because of worker error, provider timeout, malformed data, or infrastructure interruption
- **Then** the failure SHALL be observable through logs, metrics, job records, or persisted notification status

### Requirement: Catch Up Missed Alert Evaluation Windows
The system SHALL process missed five-minute alert-evaluation windows after downtime or delayed execution instead of silently skipping them, SHALL track catch-up progress independently for price-alert and news-alert jobs, and SHALL preserve distinct same-day recurring occurrences.

#### Scenario: Price-alert job resumes after downtime
- **Given** one or more five-minute price-alert evaluation windows were missed during downtime
- **When** background execution for the price-alert job resumes
- **Then** the system processes the oldest missed price-alert evaluation window first
- **And** the system continues processing missed price-alert windows in order until it catches up to the current schedule

#### Scenario: News-alert job resumes after downtime
- **Given** one or more five-minute news-alert evaluation windows were missed during downtime
- **When** background execution for the news-alert job resumes
- **Then** the system processes the oldest missed news-alert evaluation window first
- **And** the system continues processing missed news-alert windows in order until it catches up to the current schedule

#### Scenario: Catch-up processing encounters a failed window
- **Given** background execution is processing missed evaluation windows for one alert family
- **When** one catch-up evaluation window fails
- **Then** the failure SHALL remain observable
- **And** the system does not treat the failed window as successfully processed without an explicit retry or recovery path

#### Scenario: Catch-up preserves distinct same-day recurring occurrences
- **Given** a recurring alert had more than one legitimate trigger occurrence during missed windows on the same calendar day
- **When** catch-up processing evaluates those missed windows in order
- **Then** the system preserves each distinct recurring occurrence that remains eligible under the alert's re-armed state progression
- **And** the system does not collapse all same-day recurring activity into a single daily trigger

### Requirement: Run Cron-Managed Backend Jobs In A Dedicated Shared Container
The system SHALL run cron-managed backend jobs from a dedicated container runtime that supports the current scheduled alert jobs and future cron jobs through one shared scheduling pattern.

#### Scenario: Scheduled alert jobs run through the cron container
- **Given** production background execution is configured for scheduled backend jobs
- **When** the scheduled price-alert and news-alert jobs are deployed
- **Then** the system runs those jobs from the dedicated cron container rather than requiring ad hoc standalone command runtimes

#### Scenario: Additional cron jobs are added later
- **Given** the system already has cron-managed backend jobs
- **When** a new approved cron-managed backend job is introduced later
- **Then** the system supports adding that job to the shared cron container pattern without requiring a separate container by default

### Requirement: Expose Cron Container Lifecycle And Execution Logs
The system SHALL expose operator-visible logs from the cron container for startup, cron triggers, and job failures.

#### Scenario: Cron container starts
- **Given** the cron container is launched in a deployment environment
- **When** the container boots and the scheduler becomes active
- **Then** the system emits startup logs that make container initialization observable

#### Scenario: Cron trigger fires
- **Given** the cron container has one or more registered jobs
- **When** a scheduled trigger fires for one of those jobs
- **Then** the system emits logs that identify the triggered job and trigger time

#### Scenario: Cron job fails
- **Given** a registered cron-managed backend job is triggered
- **When** that job exits with an error or fails during execution
- **Then** the system emits failure logs that identify the failing job
- **And** the failure remains observable through the cron container logs

