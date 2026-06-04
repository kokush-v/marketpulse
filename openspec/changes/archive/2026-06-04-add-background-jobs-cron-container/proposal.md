## Summary

Add a dedicated cron container for backend scheduled jobs so MarketPulse runs current and future cron-triggered work from one containerized runtime with observable startup, trigger, and error logs.

## Problem

MarketPulse already has background job logic for scheduled alert evaluation, but the repository does not yet define a dedicated container runtime for cron-managed jobs. The current setup relies on a single runner command outside a shared cron-container contract, which creates a few operational gaps:

- there is no approved pattern for adding more cron jobs into one managed runtime
- startup behavior for cron infrastructure is not explicitly defined
- trigger-time logging is not consistently required
- failure visibility is left implicit instead of being part of the approved behavior

Without an explicit runtime contract, future cron additions may be implemented inconsistently across deployment environments.

## Proposed Solution

Introduce a focused background-jobs change that defines a dedicated cron container as the standard runtime for backend scheduled jobs. That container will host all approved cron-managed jobs, including the current scheduled alert evaluation job and future cron jobs added later.

The change will define observable operator-facing behavior:

- the cron container logs when it starts and when its scheduler becomes active
- each cron trigger logs which job ran and when it was triggered
- job failures remain visible through container logs

The change will also define that the container runtime is extensible enough to register more than one cron job without creating a separate container per job by default.

## Scope

- a dedicated container runtime for backend cron-managed jobs
- one shared cron container pattern for the current alert-evaluation job and future cron jobs
- startup logging for the cron container lifecycle
- trigger logging for every cron job execution
- error logging for cron job execution failures
- design guidance for job registration, logging flow, and deployment shape

## Non-Goals

- changing alert rule semantics or evaluation cadence
- adding a new queueing system or replacing existing background-job behavior outside cron-managed scheduling
- defining metrics dashboards, alerting rules, or external log aggregation products
- creating separate dedicated containers for every individual cron job
- introducing frontend behavior changes

## Impact

Affected domains:

- `background-jobs`

Primary workflows:

- operators start the cron container and can immediately see startup logs
- operators can inspect container logs to confirm each cron trigger ran
- operators can inspect container logs to diagnose job failures
- developers can add future cron jobs to one approved scheduler container pattern instead of inventing a new runtime each time

This change standardizes scheduled-job operations without changing user-facing alert behavior.
