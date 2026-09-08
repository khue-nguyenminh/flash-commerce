import uuid
from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class CouponCreate(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    discount_percent: int = Field(gt=0, le=100)
    max_usage: int = Field(gt=0)
    valid_from: datetime
    valid_to: datetime

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("valid_from", "valid_to")
    @classmethod
    def normalize_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            return (
                value.astimezone(timezone.utc)
                .replace(tzinfo=None)
            )

        return value

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.valid_to <= self.valid_from:
            raise ValueError(
                "valid_to must be later than valid_from"
            )

        return self


class CouponUpdate(CouponCreate):
    pass


class CouponResponse(BaseModel):
    id: uuid.UUID
    code: str
    discount_percent: int
    max_usage: int
    current_usage: int
    valid_from: datetime
    valid_to: datetime

    model_config = ConfigDict(from_attributes=True)