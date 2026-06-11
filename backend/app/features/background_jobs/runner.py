from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.db.session import AsyncSessionLocal
from app.features.alerts.repository import AlertRepository
from app.features.background_jobs.repository import BackgroundJobRepository
from app.features.background_jobs.service import (
    ALERT_EVALUATION_CADENCE,
    NewsScheduledAlertEvaluationService,
    PriceScheduledAlertEvaluationService,
)
from app.features.market_data.service import MarketDataService
from app.features.notifications.repository import NotificationRepository
from app.features.telegram.repository import TelegramRepository
from app.features.telegram.service import TelegramNotificationDispatcher, get_telegram_bot_app

logger = logging.getLogger("uvicorn.error")


async def _run_scheduled_alert_evaluation_once(
    service_class: type[PriceScheduledAlertEvaluationService | NewsScheduledAlertEvaluationService],
) -> int:
    bot_app = get_telegram_bot_app()
    await bot_app.initialize()
    try:
        async with AsyncSessionLocal() as session:
            service = service_class(
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


async def run_price_alert_evaluation_once() -> int:
    return await _run_scheduled_alert_evaluation_once(PriceScheduledAlertEvaluationService)


async def run_news_alert_evaluation_once() -> int:
    return await _run_scheduled_alert_evaluation_once(NewsScheduledAlertEvaluationService)


async def _run_scheduled_alert_evaluation_loop(
    run_once: Callable[[], Awaitable[int]],
    *,
    job_name: str,
) -> None:
    while True:
        processed_windows = await run_once()
        logger.info(
            "Scheduled %s alert evaluation run processed %s window(s)",
            job_name,
            processed_windows,
        )
        await asyncio.sleep(ALERT_EVALUATION_CADENCE.total_seconds())


async def run_price_alert_evaluation_loop() -> None:
    await _run_scheduled_alert_evaluation_loop(
        run_price_alert_evaluation_once,
        job_name="price",
    )


async def run_news_alert_evaluation_loop() -> None:
    await _run_scheduled_alert_evaluation_loop(
        run_news_alert_evaluation_once,
        job_name="news",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run scheduled alert evaluation jobs")
    parser.add_argument(
        "--job",
        choices=("price", "news"),
        required=True,
        help="Choose which alert-evaluation job to run.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously instead of processing due windows once",
    )
    args = parser.parse_args()

    run_once = run_price_alert_evaluation_once
    run_loop = run_price_alert_evaluation_loop
    if args.job == "news":
        run_once = run_news_alert_evaluation_once
        run_loop = run_news_alert_evaluation_loop

    if args.loop:
        asyncio.run(run_loop())
        return

    processed_windows = asyncio.run(run_once())
    logger.info(
        "Scheduled %s alert evaluation processed %s window(s)",
        args.job,
        processed_windows,
    )


if __name__ == "__main__":
    main()
