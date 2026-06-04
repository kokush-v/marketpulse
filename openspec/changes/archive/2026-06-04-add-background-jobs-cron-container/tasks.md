- [x] 1.1 Add `background-jobs` requirements for a dedicated cron container runtime and shared multi-job scheduling pattern.
- [x] 1.2 Add `background-jobs` requirements for startup, trigger, and failure log visibility through the cron container.
- [x] 1.3 Add a design document that covers container responsibilities, job registration, logging behavior, and future-job extensibility.
- [x] 1.4 Validate the OpenSpec change with `openspec validate add-background-jobs-cron-container --strict`.

- [x] 2.1 Add a Docker image and container entrypoint for backend cron-managed jobs.
- [x] 2.2 Add scheduler configuration that runs the existing scheduled alert evaluation job inside the cron container.
- [x] 2.3 Add a shared registration pattern so future cron jobs can be added to the same container without creating a new container by default.
- [x] 2.4 Add startup logs that identify container boot and scheduler activation.
- [x] 2.5 Add trigger logs that identify the job name and trigger time for every cron execution.
- [x] 2.6 Add error logs for cron job failures with enough context to identify the failing job.

- [x] 3.1 Add backend or integration tests for cron job wrapper behavior where practical.
- [x] 3.2 Validate local container configuration, including log output for startup and job execution.
- [x] 3.3 Validate the OpenSpec change with `openspec validate add-background-jobs-cron-container --strict`.
