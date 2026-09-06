import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Unicode, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Payment(Base):
    __tablename__ = "Payments"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        UNIQUEIDENTIFIER,
        primary_key=True,
        server_default=text("NEWID()"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        "OrderId",
        UNIQUEIDENTIFIER,
        ForeignKey("Orders.Id"),
        nullable=False,
    )

    payment_method: Mapped[str] = mapped_column(
        "PaymentMethod",
        Unicode(50),
        nullable=False,
    )

    transaction_id: Mapped[str | None] = mapped_column(
        "TransactionId",
        Unicode(100),
        nullable=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        "Amount",
        Numeric(18, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        "Status",
        Unicode(50),
        nullable=False,
        server_default=text("'Pending'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime,
        nullable=False,
        server_default=text("GETUTCDATE()"),
    )