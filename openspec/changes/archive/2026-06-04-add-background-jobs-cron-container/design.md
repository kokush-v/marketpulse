## Overview

This change standardizes cron-managed background execution behind one dedicated container runtime. The goal is not to redefine alert behavior, but to define how scheduled jobs are hosted, observed, and extended as MarketPulse grows from one cron job to several.

## Goals

- Run cron-managed backend jobs from one dedicated container by default.
- Keep the current scheduled alert evaluation job compatible with the shared cron container.
- Make container startup visible in logs.
- Make every cron trigger visible in logs.
- Make job failures visible in logs with the job identity.
- Keep the runtime easy to extend with additional cron jobs later.

## Non-Goals

- Replace the existing background-job business logic.
- Introduce a queue platform or job broker that is not required by the approved contract.
- Define external observability products such as CloudWatch dashboards, Datadog monitors, or pager rules.
- Force every future scheduled task into a separate service.

## Runtime Model

The implementation should use one dedicated container for cron-managed backend work. That container is responsible for:

- starting the scheduler process
- loading the approved cron job definitions
- invoking backend-owned job commands
- streaming lifecycle and execution logs to stdout or stderr so container logging can capture them

The runtime must support more than one job definition. The implementation may use a cron-compatible scheduler process, a lightweight wrapper around backend commands, or an equivalent container-native scheduling mechanism, as long as the approved behavior remains the same.

## Job Registration Model

The system should keep cron job registration centralized so new jobs can be added through one approved pattern instead of ad hoc shell commands. The exact file format is implementation-defined, but the implementation should make these concerns explicit:

- job identifier
- schedule expression
- invoked backend command
- log labeling so operators can distinguish one job from another

This allows the current alert evaluation job to become one registered entry and future jobs to be added beside it.

## Logging Model

The cron container must provide three observable logging moments:

### Container startup

When the cron container starts, logs should show:

- that the cron container booted
- that the scheduler process has started or is ready to accept schedules

### Job trigger

When a job is triggered, logs should show:

- which job was triggered
- when it was triggered
- whether execution started

### Job failure

When a job command fails, logs should show:

- which job failed
- when it failed
- the command exit failure or equivalent error context

Success logging after job completion is recommended even though the user explicitly asked only for startup, trigger, and error visibility.

## Ownership And Security

Cron-managed jobs remain backend-owned. The cron container must use backend-managed environment variables and credentials only. It must not rely on client-provided identifiers or frontend-controlled inputs for scheduled execution decisions.

For the existing alert evaluation job, all current ownership guarantees remain unchanged:

- alert ownership still comes from persisted backend data
- Telegram routing still comes from trusted persisted linkage data
- user-facing requests do not directly trigger privileged cron execution paths

## Deployment Guidance

The approved contract assumes the cron runtime is a separate deployable container from the HTTP API container. This separation keeps request-serving concerns independent from scheduler concerns and makes cron logs easier to inspect.

The implementation may share the same application image build inputs as the backend API if operationally practical, but the runtime command, entrypoint, or scheduler configuration should be specific to the cron container role.

## Risks

- A misconfigured schedule registry could prevent one or more jobs from running.
- Poorly labeled logs could make multi-job debugging difficult as more cron jobs are added.
- If the scheduler process exits silently, jobs may stop running unless startup and failure logs are clear.

## Rollback

If this change must be rolled back, the dedicated cron container and its schedule registry can be removed while leaving the underlying backend job logic intact. Any rollback should preserve the approved alert-evaluation behavior that already exists outside this runtime-shape change.
