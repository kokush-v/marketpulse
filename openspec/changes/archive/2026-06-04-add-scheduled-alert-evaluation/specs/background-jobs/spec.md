## ADDED Requirements

### Requirement: Evaluate Alerts Every Five Minutes Outside User Requests
The system SHALL run alert evaluation through background execution on a five-minute cadence rather than during user-facing request-response flows.

#### Scenario: Scheduled evaluation runs on cadence
- **Given** production background execution is configured for alerts
- **When** the next five-minute evaluation window arrives
- **Then** the system evaluates eligible alerts in background execution without requiring a user-facing request

#### Scenario: Evaluation failure remains observable
- **Given** production background execution is configured for alerts
- **When** a scheduled alert-evaluation run fails because of worker error, provider timeout, malformed data, or infrastructure interruption
- **Then** the failure SHALL be observable through logs, metrics, job records, or persisted notification status

### Requirement: Catch Up Missed Alert Evaluation Windows
The system SHALL process missed five-minute alert-evaluation windows after downtime or delayed execution instead of silently skipping them.

#### Scenario: System resumes after downtime
- **Given** one or more five-minute alert-evaluation windows were missed during downtime
- **When** background execution resumes
- **Then** the system processes the oldest missed evaluation window first
- **And** the system continues processing missed windows in order until it catches up to the current schedule

#### Scenario: Catch-up processing encounters a failed window
- **Given** background execution is processing missed evaluation windows
- **When** one catch-up evaluation window fails
- **Then** the failure SHALL remain observable
- **And** the system does not treat the failed window as successfully processed without an explicit retry or recovery path
