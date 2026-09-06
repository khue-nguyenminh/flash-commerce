import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Unicode, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Order(Base):
    __tablename__ = "Orders"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        UNIQUEIDENTIFIER,
        primary_key=True,
        server_default=text("NEWID()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        "UserId",
        UNIQUEIDENTIFIER,
        ForeignKey("Users.Id"),
        nullable=False,
    )

    address_id: Mapped[uuid.UUID] = mapped_column(
        "AddressId",
        UNIQUEIDENTIFIER,
        ForeignKey("Addresses.Id"),
        nullable=False,
    )

    coupon_id: Mapped[uuid.UUID | None] = mapped_column(
        "CouponId",
        UNIQUEIDENTIFIER,
        ForeignKey("Coupons.Id"),
        nullable=True,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        "TotalAmount",
        Numeric(18, 2),
        nullable=False,
    )

    final_amount: Mapped[Decimal] = mapped_column(
        "FinalAmount",
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