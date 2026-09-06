import uuid
from sqlalchemy import ForeignKey, Unicode, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Category(Base):
    __tablename__ = "Categories"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        UNIQUEIDENTIFIER,
        primary_key= True,
        server_default = text("NEWID()"),
    )
    name: Mapped[str] = mapped_column(
        "Name",
        Unicode(100),
        nullable = False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        "ParentId",
        UNIQUEIDENTIFIER,
        ForeignKey("Categories.Id"),
        nullable = True,
    )
    slug: Mapped[StopIteration] = mapped_column(
        "Slug",
        Unicode(100),
       unique = True,
       nullable = False,
    )