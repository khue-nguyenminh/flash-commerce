import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    UnicodeText,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Review(Base):
    __tablename__ = "Reviews"

    __table_args__ = (
        CheckConstraint(
            "Rating >= 1 AND Rating <= 5",
            name="ck_reviews_rating",
        ),
        UniqueConstraint(
            "UserId",
            "ProductId",
            name="uq_reviews_user_product",
        ),
    )

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

    product_id: Mapped[uuid.UUID] = mapped_column(
        "ProductId",
        UNIQUEIDENTIFIER,
        ForeignKey("Products.Id"),
        nullable=False,
    )

    rating: Mapped[int] = mapped_column(
        "Rating",
        Integer,
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        "Comment",
        UnicodeText,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime,
        nullable=False,
        server_default=text("GETUTCDATE()"),
    )