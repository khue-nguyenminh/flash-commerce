import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OrderItem(Base):
    __tablename__ = "OrderItems"

    __table_args__ = (
        CheckConstraint(
            "Quantity > 0",
            name="ck_order_items_quantity",
        ),
    )

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

    product_id: Mapped[uuid.UUID] = mapped_column(
        "ProductId",
        UNIQUEIDENTIFIER,
        ForeignKey("Products.Id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        "Quantity",
        Integer,
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        "UnitPrice",
        Numeric(18, 2),
        nullable=False,
    )