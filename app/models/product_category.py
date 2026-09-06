import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProductCategory(Base):
    __tablename__ = "ProductCategories"

    product_id: Mapped[uuid.UUID] = mapped_column(
        "ProductId",
        UNIQUEIDENTIFIER,
        ForeignKey("Products.Id"),
        primary_key=True,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        "CategoryId",
        UNIQUEIDENTIFIER,
        ForeignKey("Categories.Id"),
        primary_key=True,
    )