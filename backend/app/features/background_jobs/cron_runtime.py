from __future__ import annotations

import asyncio
import logging

from app.features.background_jobs.cron_registry import get_registered_cron_jobs
from app.features.background_jobs.cron_scheduler import CronScheduler

LOGGER_NAME = "marketpulse.cron"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main() -> None:
    configure_logging()
    logger = logging.getLogger(LOGGER_NAME)
    jobs = get_registered_cron_jobs()
    logger.info("Cron container booted")
    logger.info("Cron container loaded %s job(s)", len(jobs))
    scheduler = CronScheduler(jobs=jobs)
    asyncio.run(scheduler.run_forever())


if __name__ == "__main__":
    main()
