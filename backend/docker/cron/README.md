# Cron Container

This folder contains the Docker runtime for backend cron-managed jobs.

- `Dockerfile` builds the cron container image
- `entrypoint.sh` starts the cron runtime inside the container

The scheduler logic and job registry live in:

- `app/features/background_jobs/cron_runtime.py`
- `app/features/background_jobs/cron_registry.py`
- `app/features/background_jobs/cron_scheduler.py`
