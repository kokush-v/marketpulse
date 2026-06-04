from __future__ import annotations

import argparse
import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.features.alerts.repository import AlertRepository
from app.features.background_jobs.repository import BackgroundJobRepository
from app.features.background_jobs.service import (
    ALERT_EVALUATION_CADENCE,
    ScheduledAlertEvaluationService,
)
from app.features.market_data.service import MarketDataService
from app.features.notifications.repository import NotificationRepository
from app.features.telegram.repository import TelegramRepository
from app.features.telegram.service import TelegramNotificationDispatcher, get_telegram_bot_app

logger = logging.getLogger("uvicorn.error")


async def run_scheduled_alert_evaluation_once() -> int:
    bot_app = get_telegram_bot_app()
    await bot_app.initialize()
    try:
        async with AsyncSessionLocal() as session:
            service = ScheduledAlertEvaluationService(
                alert_repository=AlertRepository(session),
                job_repository=BackgroundJobRepository(session),
                market_data_service=MarketDataService(),
                telegram_dispatcher=TelegramNotificationDispatcher(
                    TelegramRepository(session),
                    NotificationRepository(session),
                    bot_app,
                ),
            )
            return await service.run_due_windows()
    finally:
        await bot_app.shutdown()


async def run_scheduled_alert_evaluation_loop() -> None:
    while True:
        processed_windows = await run_scheduled_alert_evaluation_once()
        logger.info("Scheduled alert evaluation run processed %s window(s)", processed_windows)
        await asyncio.sleep(ALERT_EVALUATION_CADENCE.total_seconds())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run scheduled alert evaluation jobs")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously instead of processing due windows once",
    )
    args = parser.parse_args()

    if args.loop:
        asyncio.run(run_scheduled_alert_evaluation_loop())
        return

    processed_windows = asyncio.run(run_scheduled_alert_evaluation_once())
    logger.info("Scheduled alert evaluation processed %s window(s)", processed_windows)


if __name__ == "__main__":
    main()
