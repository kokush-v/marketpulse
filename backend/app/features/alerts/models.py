import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused')", name="ck_alert_rules_status"),
        CheckConstraint("symbol = upper(symbol)", name="ck_alert_rules_symbol_uppercase"),
        CheckConstraint(
            "jsonb_typeof(scenario_payload) = 'object'",
            name="ck_alert_rules_scenario_object",
        ),
        CheckConstraint(
            "time_behavior IN ('one_time', 'daily_recurring')",
            name="ck_alert_rules_time_behavior",
        ),
        CheckConstraint(
            "(time_behavior = 'one_time' AND recurring_start_date IS NULL AND "
            "recurring_end_date IS NULL) OR (time_behavior = 'daily_recurring' "
            "AND recurring_start_date IS NOT NULL AND recurring_end_date IS NOT NULL "
            "AND recurring_end_date >= recurring_start_date)",
            name="ck_alert_rules_recurring_window",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[str] = mapped_column(String(120), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    time_behavior: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'one_time'"),
    )
    recurring_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recurring_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_triggered_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    scenario_payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
