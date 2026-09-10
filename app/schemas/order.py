import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    address_id: uuid.UUID
    items: list[OrderItemCreate] = Field(min_length=1)
    coupon_code: str | None = Field(
        default=None,
        max_length=20,
    )

    @field_validator("coupon_code")
    @classmethod
    def normalize_coupon_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_code = value.strip().upper()

        return normalized_code or None

    @model_validator(mode="after")
    def validate_unique_products(self):
        product_ids = [
            item.product_id
            for item in self.items
        ]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError(
                "Each product may appear only once in an order"
            )

        return self


class OrderItemResponse(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    address_id: uuid.UUID
    total_amount: Decimal
    coupon_id: uuid.UUID | None
    final_amount: Decimal
    status: str
    created_at: datetime
    items: list[OrderItemResponse]

class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    page: int
    page_size: int
    total: int

class OrderStatusUpdate(BaseModel):
    status: Literal[
        "Processing",
        "Shipped",
        "Completed",
    ]