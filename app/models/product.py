import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, Unicode, UnicodeText, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Product(Base):
    __tablename__ = "Products"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        UNIQUEIDENTIFIER,
        primary_key=True,
        server_default=text("NEWID()"),
    )

    name: Mapped[str] = mapped_column(
        "Name",
        Unicode(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        "Description",
        UnicodeText,
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(
        "Price",
        Numeric(18, 2),
        nullable=False,
    )

    stock_quantity: Mapped[int] = mapped_column(
        "StockQuantity",
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    is_flash_sale: Mapped[bool] = mapped_column(
        "IsFlashSale",
        Boolean,
        nullable=False,
        server_default=text("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime,
        nullable=False,
        server_default=text("GETUTCDATE()"),
    )