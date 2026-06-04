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


def test_registered_cron_jobs_include_scheduled_alert_evaluation() -> None:
    jobs = get_registered_cron_jobs()

    assert len(jobs) == 1
    assert jobs[0].name == "scheduled-alert-evaluation"
    assert jobs[0].schedule.expression == "*/5 * * * *"
    assert jobs[0].command == ("python", "-m", "app.features.background_jobs.runner")


def test_cron_expression_matches_every_five_minutes() -> None:
    expression = CronExpression.parse("*/5 * * * *")

    assert expression.matches(datetime(2026, 6, 4, 10, 0, tzinfo=UTC))
    assert expression.matches(datetime(2026, 6, 4, 10, 5, tzinfo=UTC))
    assert not expression.matches(datetime(2026, 6, 4, 10, 3, tzinfo=UTC))


@pytest.mark.asyncio
async def test_command_runner_logs_trigger_and_failure(
    caplog, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeProcess:
        async def wait(self) -> int:
            return 2

    async def fake_create_subprocess_exec(*args: str):
        assert args == ("python", "-m", "app.features.background_jobs.runner")
        return FakeProcess()

    monkeypatch.setattr(
        "app.features.background_jobs.cron_scheduler.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    runner = CronCommandRunner()
    job = RegisteredCronJob(
        name="scheduled-alert-evaluation",
        schedule=CronExpression.parse("*/5 * * * *"),
        command=("python", "-m", "app.features.background_jobs.runner"),
    )

    with caplog.at_level("INFO", logger="marketpulse.cron"):
        result = await runner.run(job, triggered_at=datetime(2026, 6, 4, 10, 0, tzinfo=UTC))

    assert result == 2
    assert "triggered at 2026-06-04T10:00:00+00:00" in caplog.text
    assert "failed at 2026-06-04T10:00:00+00:00 with exit code 2" in caplog.text


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
        name="scheduled-alert-evaluation",
        schedule=CronExpression.parse("*/5 * * * *"),
        command=("python", "-m", "app.features.background_jobs.runner"),
    )

    with caplog.at_level("INFO", logger="marketpulse.cron"):
        result = await runner.run(job, triggered_at=datetime(2026, 6, 4, 10, 0, tzinfo=UTC))

    assert result == 1
    assert "failed to start at 2026-06-04T10:00:00+00:00" in caplog.text


@pytest.mark.asyncio
async def test_scheduler_suppresses_unexpected_runner_failure(caplog) -> None:
    class ExplodingRunner:
        async def run(self, job: RegisteredCronJob, *, triggered_at: datetime) -> int:
            _ = job, triggered_at
            raise RuntimeError("unexpected failure")

    job = RegisteredCronJob(
        name="scheduled-alert-evaluation",
        schedule=CronExpression.parse("*/5 * * * *"),
        command=("python", "-m", "app.features.background_jobs.runner"),
    )
    scheduler = CronScheduler(jobs=(job,), runner=ExplodingRunner())

    with caplog.at_level("INFO", logger="marketpulse.cron"):
        await scheduler._run_matching_jobs(datetime(2026, 6, 4, 10, 0, tzinfo=UTC))

    assert "suppressed an unexpected failure" in caplog.text
