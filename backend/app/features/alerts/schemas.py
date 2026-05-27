from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

AlertScenario = Literal["price_above", "price_below", "coin_news"]
TriggerMode = Literal["currency", "percent"]
AlertTimeBehavior = Literal["one_time", "daily_recurring"]
AlertStatus = Literal["active", "paused"]
AlertAction = Literal["edit", "pause", "resume", "delete"]


class AlertAssetPayload(BaseModel):
    asset_id: str = Field(min_length=1, max_length=120)
    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    image_url: str | None = Field(default=None, max_length=500)


class AlertUpsertRequest(AlertAssetPayload):
    scenario: AlertScenario
    time_behavior: AlertTimeBehavior = "one_time"
    recurring_start_date: date | None = None
    recurring_end_date: date | None = None
    trigger_mode: TriggerMode | None = None
    threshold_value: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_trigger_configuration(self) -> "AlertUpsertRequest":
        if self.time_behavior == "daily_recurring":
            if self.recurring_start_date is None or self.recurring_end_date is None:
                raise ValueError("Recurring alerts require both a start date and an end date")
            if self.recurring_end_date < self.recurring_start_date:
                raise ValueError("Recurring alert end date must be on or after the start date")
        elif self.recurring_start_date is not None or self.recurring_end_date is not None:
            raise ValueError("One-time alerts do not accept recurring dates")

        if self.scenario == "coin_news":
            if self.trigger_mode is not None or self.threshold_value is not None:
                raise ValueError("News alerts do not accept trigger mode or threshold value")
            return self

        if self.trigger_mode is None:
            raise ValueError("Price alerts require a trigger mode")
        if self.threshold_value is None:
            raise ValueError("Price alerts require a threshold value")
        return self


class CreateAlertRequest(AlertUpsertRequest):
    pass


class UpdateAlertRequest(AlertUpsertRequest):
    pass


class AlertResponse(BaseModel):
    id: UUID
    asset_id: str
    symbol: str
    name: str
    image_url: str | None = None
    status: AlertStatus
    scenario: AlertScenario
    time_behavior: AlertTimeBehavior
    recurring_start_date: date | None = None
    recurring_end_date: date | None = None
    trigger_mode: TriggerMode | None = None
    threshold_value: float | None = None
    baseline_price: float | None = None
    rule_summary: str
    time_summary: str
    available_actions: list[AlertAction]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertResponse]


class AlertOperationResponse(BaseModel):
    success: bool


class AlertErrorResponse(BaseModel):
    message: str
