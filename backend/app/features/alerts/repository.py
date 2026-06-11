import uuid
from datetime import date, datetime

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.alerts.models import AlertRule


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_alerts_for_user(self, user_id: uuid.UUID) -> list[AlertRule]:
        stmt = (
            select(AlertRule)
            .where(AlertRule.user_id == user_id)
            .order_by(AlertRule.created_at.desc(), AlertRule.name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_alert_for_user(self, user_id: uuid.UUID, alert_id: uuid.UUID) -> AlertRule | None:
        stmt = select(AlertRule).where(AlertRule.user_id == user_id, AlertRule.id == alert_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_eligible_price_alerts_for_window(self, window_date: date) -> list[AlertRule]:
        return await self._list_eligible_alerts_for_window(
            window_date,
            scenarios=("price_above", "price_below"),
        )

    async def list_eligible_news_alerts_for_window(self, window_date: date) -> list[AlertRule]:
        return await self._list_eligible_alerts_for_window(
            window_date,
            scenarios=("coin_news",),
        )

    async def _list_eligible_alerts_for_window(
        self,
        window_date: date,
        *,
        scenarios: tuple[str, ...],
    ) -> list[AlertRule]:
        stmt = (
            select(AlertRule)
            .where(
                AlertRule.status == "active",
                AlertRule.scenario_payload["scenario"].astext.in_(scenarios),
                (
                    (AlertRule.time_behavior == "one_time")
                    | (
                        (AlertRule.time_behavior == "daily_recurring")
                        & (AlertRule.recurring_start_date <= window_date)
                        & (AlertRule.recurring_end_date >= window_date)
                    )
                ),
            )
            .order_by(AlertRule.created_at.asc(), AlertRule.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_alert(
        self,
        *,
        user_id: uuid.UUID,
        asset_id: str,
        symbol: str,
        name: str,
        image_url: str | None,
        time_behavior: str,
        recurring_start_date,
        recurring_end_date,
        scenario_payload: dict[str, object],
    ) -> AlertRule:
        stmt = (
            insert(AlertRule)
            .values(
                user_id=user_id,
                asset_id=asset_id,
                symbol=symbol,
                name=name,
                image_url=image_url,
                time_behavior=time_behavior,
                recurring_start_date=recurring_start_date,
                recurring_end_date=recurring_end_date,
                scenario_payload=scenario_payload,
                status="active",
            )
            .returning(AlertRule)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def update_alert(
        self,
        alert: AlertRule,
        *,
        asset_id: str,
        symbol: str,
        name: str,
        image_url: str | None,
        time_behavior: str,
        recurring_start_date,
        recurring_end_date,
        scenario_payload: dict[str, object],
    ) -> AlertRule:
        stmt = (
            update(AlertRule)
            .where(AlertRule.id == alert.id)
            .values(
                asset_id=asset_id,
                symbol=symbol,
                name=name,
                image_url=image_url,
                time_behavior=time_behavior,
                recurring_start_date=recurring_start_date,
                recurring_end_date=recurring_end_date,
                scenario_payload=scenario_payload,
                updated_at=func.now(),
            )
            .returning(AlertRule)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def set_alert_status(
        self,
        alert: AlertRule,
        status: str,
    ) -> AlertRule:
        stmt = (
            update(AlertRule)
            .where(AlertRule.id == alert.id)
            .values(status=status, updated_at=func.now())
            .returning(AlertRule)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def resume_rearmed_one_time_alert(
        self,
        alert: AlertRule,
        *,
        scenario_payload: dict[str, object],
        arm_version: int,
    ) -> AlertRule:
        stmt = (
            update(AlertRule)
            .where(AlertRule.id == alert.id)
            .values(
                status="active",
                scenario_payload=scenario_payload,
                last_triggered_on=None,
                last_triggered_at=None,
                arm_version=arm_version,
                updated_at=func.now(),
            )
            .returning(AlertRule)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def update_alert_runtime_state(
        self,
        alert: AlertRule,
        *,
        scenario_payload: dict[str, object],
    ) -> AlertRule:
        stmt = (
            update(AlertRule)
            .where(AlertRule.id == alert.id)
            .values(
                scenario_payload=scenario_payload,
                updated_at=func.now(),
            )
            .returning(AlertRule)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def record_trigger_result(
        self,
        alert: AlertRule,
        *,
        triggered_at: datetime,
        scenario_payload: dict[str, object],
        pause_after_trigger: bool,
    ) -> AlertRule:
        values: dict[str, object] = {
            "last_triggered_on": triggered_at.date(),
            "last_triggered_at": triggered_at,
            "scenario_payload": scenario_payload,
            "updated_at": func.now(),
        }
        if pause_after_trigger:
            values["status"] = "paused"

        stmt = (
            update(AlertRule).where(AlertRule.id == alert.id).values(**values).returning(AlertRule)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def delete_alert_for_user(self, user_id: uuid.UUID, alert_id: uuid.UUID) -> bool:
        stmt = delete(AlertRule).where(AlertRule.user_id == user_id, AlertRule.id == alert_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return bool(result.rowcount)
