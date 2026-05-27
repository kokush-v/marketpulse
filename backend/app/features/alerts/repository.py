import uuid

from sqlalchemy import delete, select
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
        alert = AlertRule(
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
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

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
        alert.asset_id = asset_id
        alert.symbol = symbol
        alert.name = name
        alert.image_url = image_url
        alert.time_behavior = time_behavior
        alert.recurring_start_date = recurring_start_date
        alert.recurring_end_date = recurring_end_date
        alert.scenario_payload = scenario_payload
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def set_alert_status(self, alert: AlertRule, status: str) -> AlertRule:
        alert.status = status
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def delete_alert_for_user(self, user_id: uuid.UUID, alert_id: uuid.UUID) -> bool:
        stmt = delete(AlertRule).where(AlertRule.user_id == user_id, AlertRule.id == alert_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return bool(result.rowcount)
