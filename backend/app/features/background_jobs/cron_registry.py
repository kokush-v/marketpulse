from __future__ import annotations

from app.features.background_jobs.cron_scheduler import CronExpression, RegisteredCronJob


def get_registered_cron_jobs() -> tuple[RegisteredCronJob, ...]:
    return (
        RegisteredCronJob(
            name="scheduled-price-alert-evaluation",
            schedule=CronExpression.parse("*/5 * * * *"),
            command=("python", "-m", "app.features.background_jobs.runner", "--job", "price"),
        ),
        RegisteredCronJob(
            name="scheduled-news-alert-evaluation",
            schedule=CronExpression.parse("*/5 * * * *"),
            command=("python", "-m", "app.features.background_jobs.runner", "--job", "news"),
        ),
    )
