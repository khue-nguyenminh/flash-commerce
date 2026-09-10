import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    order_id: uuid.UUID
    payment_method: Literal[
        "Card",
        "BankTransfer",
        "EWallet",
    ]


class PaymentResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    payment_method: str
    transaction_id: str | None
    amount: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)