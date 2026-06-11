from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.features.background_jobs.cron_registry import get_registered_cron_jobs
from app.features.background_jobs.cron_scheduler import (
    CronCommandRunner,
    CronExpression,
    CronScheduler,
    RegisteredCronJob,
)


def test_registered_cron_jobs_include_split_alert_evaluation_jobs() -> None:
    jobs = get_registered_cron_jobs()
    scheduled_price_job = next(
        (job for job in jobs if job.name == "scheduled-price-alert-evaluation"),
        None,
    )
    scheduled_news_job = next(
        (job for job in jobs if job.name == "scheduled-news-alert-evaluation"),
        None,
    )

    assert scheduled_price_job is not None
    assert scheduled_news_job is not None
    assert scheduled_price_job.schedule.expression == "*/5 * * * *"
    assert scheduled_news_job.schedule.expression == "*/5 * * * *"
    assert scheduled_price_job.command == (
        "python",
        "-m",
        "app.features.background_jobs.runner",
        "--job",
        "price",
    )
    assert scheduled_news_job.command == (
        "python",
        "-m",
        "app.features.background_jobs.runner",
        "--job",
        "news",
    )


def test_cron_expression_matches_every_five_minutes() -> None:
    expression = CronExpression.parse("*/5 * * * *")

    assert expression.matches(datetime(2026, 6, 4, 10, 0, tzinfo=UTC))
    assert expression.matches(datetime(2026, 6, 4, 10, 5, tzinfo=UTC))
    assert not expression.matches(datetime(2026, 6, 4, 10, 3, tzinfo=UTC))


def test_cron_expression_rejects_single_value_step_syntax() -> None:
    with pytest.raises(ValueError, match="requires '\\*' or a numeric range base"):
        CronExpression.parse("5/10 * * * *")


@pytest.mark.asyncio
async def test_command_runner_logs_trigger_and_failure(
    caplog, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeProcess:
        async def wait(self) -> int:
            return 2

    async def fake_create_subprocess_exec(*args: str):
        assert args == ("python", "-m", "app.features.background_jobs.runner", "--job", "price")
        return FakeProcess()

    monkeypatch.setattr(
        "app.features.background_jobs.cron_scheduler.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    runner = CronCommandRunner()
    job = RegisteredCronJob(
        name="scheduled-price-alert-evaluation",
        schedule=CronExpression.parse("*/5 * * * *"),
        command=("python", "-m", "app.features.background_jobs.runner", "--job", "price"),
    )

    with caplog.at_level("INFO", logger="marketpulse.cron"):
        result = await runner.run(job, triggered_at=datetime(2026, 6, 4, 10, 0, tzinfo=UTC))

    assert result == 2
    assert "triggered at 2026-06-04T10:00:00+00:00" in caplog.text
    assert "failed at " in caplog.text
    assert "for trigger 2026-06-04T10:00:00+00:00 with exit code 2" in caplog.text


@pytest.mark.asyncio
async def test_command_runner_logs_startup_failure_without_raising(
    caplog, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_create_subprocess_exec(*args: str):
        _ = args
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.features.background_jobs.cron_scheduler.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    runner = CronCommandRunner()
    job = RegisteredCronJob(
        name="scheduled-news-alert-evaluation",
        schedule=CronExpression.parse("*/5 * * * *"),
        command=("python", "-m", "app.features.background_jobs.runner", "--job", "news"),
    )

    with caplog.at_level("INFO", logger="marketpulse.cron"):
        result = await runner.run(job, triggered_at=datetime(2026, 6, 4, 10, 0, tzinfo=UTC))

    assert result == 1
    assert "failed to start at " in caplog.text
    assert "for trigger 2026-06-04T10:00:00+00:00" in caplog.text


@pytest.mark.asyncio
async def test_scheduler_suppresses_unexpected_runner_failure(caplog) -> None:
    class ExplodingRunner:
        async def run(self, job: RegisteredCronJob, *, triggered_at: datetime) -> int:
            _ = job, triggered_at
            raise RuntimeError("unexpected failure")

    job = RegisteredCronJob(
        name="scheduled-price-alert-evaluation",
        schedule=CronExpression.parse("*/5 * * * *"),
        command=("python", "-m", "app.features.background_jobs.runner", "--job", "price"),
    )
    scheduler = CronScheduler(jobs=(job,), runner=ExplodingRunner())

    with caplog.at_level("INFO", logger="marketpulse.cron"):
        await scheduler._run_matching_jobs(datetime(2026, 6, 4, 10, 0, tzinfo=UTC))

    assert "suppressed an unexpected failure" in caplog.text


@pytest.mark.asyncio
async def test_scheduler_does_not_backfill_missed_minutes(monkeypatch: pytest.MonkeyPatch) -> None:
    class RecordingRunner:
        def __init__(self) -> None:
            self.triggered_at_values: list[datetime] = []

        async def run(self, job: RegisteredCronJob, *, triggered_at: datetime) -> int:
            _ = job
            self.triggered_at_values.append(triggered_at)
            return 0

    class StopLoop(Exception):
        pass

    state = {"tick": 0}

    def fake_clock() -> datetime:
        if state["tick"] == 0:
            return datetime(2026, 6, 4, 10, 0, 30, tzinfo=UTC)
        return datetime(2026, 6, 4, 10, 3, 0, tzinfo=UTC)

    async def fake_sleep(_: float) -> None:
        if state["tick"] == 0:
            state["tick"] = 1
            return
        raise StopLoop

    runner = RecordingRunner()
    scheduler = CronScheduler(
        jobs=(
            RegisteredCronJob(
                name="every-minute-job",
                schedule=CronExpression.parse("* * * * *"),
                command=("python", "-m", "app.features.background_jobs.runner"),
            ),
        ),
        runner=runner,
        clock=fake_clock,
    )
    monkeypatch.setattr("app.features.background_jobs.cron_scheduler.asyncio.sleep", fake_sleep)

    with pytest.raises(StopLoop):
        await scheduler.run_forever()

    assert runner.triggered_at_values == [
        datetime(2026, 6, 4, 10, 0, tzinfo=UTC),
        datetime(2026, 6, 4, 10, 3, tzinfo=UTC),
    ]
