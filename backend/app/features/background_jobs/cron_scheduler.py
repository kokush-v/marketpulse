from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger("marketpulse.cron")


class CronField:
    def __init__(self, expression: str, *, minimum: int, maximum: int) -> None:
        self.expression = expression
        self.minimum = minimum
        self.maximum = maximum
        self.allowed_values = self._parse(expression)

    def matches(self, value: int) -> bool:
        return value in self.allowed_values

    def _parse(self, expression: str) -> set[int]:
        allowed: set[int] = set()
        for part in expression.split(","):
            allowed.update(self._parse_part(part.strip()))
        if not allowed:
            raise ValueError(f"Invalid cron field expression: {expression!r}")
        return allowed

    def _parse_part(self, part: str) -> set[int]:
        if not part:
            raise ValueError("Cron field part cannot be empty")

        if "/" in part:
            base, step_value = part.split("/", maxsplit=1)
            step = int(step_value)
            if step <= 0:
                raise ValueError("Cron step must be positive")
            if base != "*" and "-" not in base:
                raise ValueError("Cron step syntax requires '*' or a numeric range base")
        else:
            base = part
            step = 1

        if base == "*":
            start = self.minimum
            end = self.maximum
        elif "-" in base:
            start_value, end_value = base.split("-", maxsplit=1)
            start = int(start_value)
            end = int(end_value)
        else:
            value = int(base)
            self._validate_range(value, value)
            return {value}

        self._validate_range(start, end)
        return set(range(start, end + 1, step))

    def _validate_range(self, start: int, end: int) -> None:
        if start < self.minimum or end > self.maximum or start > end:
            raise ValueError(
                f"Cron field range {start}-{end} is outside {self.minimum}-{self.maximum}"
            )


@dataclass(frozen=True)
class CronExpression:
    expression: str
    minute: CronField
    hour: CronField
    day_of_month: CronField
    month: CronField
    day_of_week: CronField

    @classmethod
    def parse(cls, expression: str) -> CronExpression:
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError("Cron expressions must have five fields")

        minute, hour, day_of_month, month, day_of_week = parts
        return cls(
            expression=expression,
            minute=CronField(minute, minimum=0, maximum=59),
            hour=CronField(hour, minimum=0, maximum=23),
            day_of_month=CronField(day_of_month, minimum=1, maximum=31),
            month=CronField(month, minimum=1, maximum=12),
            day_of_week=CronField(day_of_week, minimum=0, maximum=6),
        )

    def matches(self, value: datetime) -> bool:
        normalized = value.astimezone(UTC)
        cron_weekday = (normalized.weekday() + 1) % 7
        return (
            self.minute.matches(normalized.minute)
            and self.hour.matches(normalized.hour)
            and self.day_of_month.matches(normalized.day)
            and self.month.matches(normalized.month)
            and self.day_of_week.matches(cron_weekday)
        )


@dataclass(frozen=True)
class RegisteredCronJob:
    name: str
    schedule: CronExpression
    command: tuple[str, ...]


class CronCommandRunner:
    async def run(self, job: RegisteredCronJob, *, triggered_at: datetime) -> int:
        trigger_iso = triggered_at.astimezone(UTC).isoformat()
        logger.info("Cron job '%s' triggered at %s", job.name, trigger_iso)
        try:
            process = await asyncio.create_subprocess_exec(*job.command)
        except Exception:
            failure_iso = datetime.now(tz=UTC).isoformat()
            logger.exception(
                "Cron job '%s' failed to start at %s for trigger %s",
                job.name,
                failure_iso,
                trigger_iso,
            )
            return 1
        return_code = await process.wait()
        completed_iso = datetime.now(tz=UTC).isoformat()

        if return_code != 0:
            logger.error(
                "Cron job '%s' failed at %s for trigger %s with exit code %s",
                job.name,
                completed_iso,
                trigger_iso,
                return_code,
            )
            return return_code

        logger.info(
            "Cron job '%s' completed successfully at %s for trigger %s",
            job.name,
            completed_iso,
            trigger_iso,
        )
        return return_code


class CronScheduler:
    def __init__(
        self,
        *,
        jobs: Iterable[RegisteredCronJob],
        runner: CronCommandRunner | None = None,
        clock: Callable[[], datetime] | None = None,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self.jobs = tuple(jobs)
        self.runner = runner or CronCommandRunner()
        self.clock = clock or (lambda: datetime.now(tz=UTC))
        self.poll_interval_seconds = poll_interval_seconds

    async def run_forever(self) -> None:
        logger.info("Cron scheduler started with %s registered job(s)", len(self.jobs))
        last_processed_minute: datetime | None = None

        while True:
            current_minute = self._truncate_to_minute(self.clock())
            if last_processed_minute != current_minute:
                await self._run_matching_jobs(current_minute)
                last_processed_minute = current_minute

            await asyncio.sleep(self.poll_interval_seconds)

    async def _run_matching_jobs(self, current_minute: datetime) -> None:
        for job in self.jobs:
            if job.schedule.matches(current_minute):
                try:
                    await self.runner.run(job, triggered_at=current_minute)
                except Exception:
                    logger.exception(
                        "Cron scheduler suppressed an unexpected failure for job '%s' at %s",
                        job.name,
                        current_minute.astimezone(UTC).isoformat(),
                    )

    def _truncate_to_minute(self, value: datetime) -> datetime:
        return value.astimezone(UTC).replace(second=0, microsecond=0)
