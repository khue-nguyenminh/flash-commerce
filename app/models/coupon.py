import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, Unicode, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Coupon(Base):
    __tablename__ = "Coupons"

    __table_args__ = (
        CheckConstraint(
            "DiscountPercent > 0 AND DiscountPercent <= 100",
            name="ck_coupons_discount_percent",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        UNIQUEIDENTIFIER,
        primary_key=True,
        server_default=text("NEWID()"),
    )

    code: Mapped[str] = mapped_column(
        "Code",
        Unicode(20),
        unique=True,
        nullable=False,
    )

    discount_percent: Mapped[int] = mapped_column(
        "DiscountPercent",
        Integer,
        nullable=False,
    )

    max_usage: Mapped[int] = mapped_column(
        "MaxUsage",
        Integer,
        nullable=False,
    )

    current_usage: Mapped[int] = mapped_column(
        "CurrentUsage",
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    valid_from: Mapped[datetime] = mapped_column(
        "ValidFrom",
        DateTime,
        nullable=False,
    )

    valid_to: Mapped[datetime] = mapped_column(
        "ValidTo",
        DateTime,
        nullable=False,
    )