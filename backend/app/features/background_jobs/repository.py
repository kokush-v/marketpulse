from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.background_jobs.models import BackgroundJobCursor


class BackgroundJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_cursor(self, name: str) -> BackgroundJobCursor | None:
        stmt = select(BackgroundJobCursor).where(BackgroundJobCursor.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def ensure_cursor(
        self,
        *,
        name: str,
        default_last_processed_window_end: datetime | None,
    ) -> BackgroundJobCursor:
        stmt = (
            insert(BackgroundJobCursor)
            .values(
                name=name,
                last_processed_window_end=default_last_processed_window_end,
            )
            .on_conflict_do_nothing(index_elements=["name"])
        )
        await self.session.execute(stmt)
        await self.session.commit()

        cursor = await self.get_cursor(name)
        if cursor is None:
            raise RuntimeError("Background job cursor could not be created")
        return cursor

    async def advance_cursor(
        self,
        *,
        name: str,
        last_processed_window_end: datetime,
    ) -> BackgroundJobCursor:
        stmt = (
            update(BackgroundJobCursor)
            .where(BackgroundJobCursor.name == name)
            .values(last_processed_window_end=last_processed_window_end)
            .returning(BackgroundJobCursor)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
