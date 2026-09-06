import uuid
from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, Unicode, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Address(Base):
    __tablename__ = "Addresses"
    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        UNIQUEIDENTIFIER,
        primary_key= True,
        server_default = text("NEWID()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        "UserId",
        UNIQUEIDENTIFIER,
        ForeignKey("Users.Id"),
        nullable = False,
    )
    full_name: Mapped[str] = mapped_column(
        "PhoneNumber",
        Unicode(20),
        nullable = False,
    )
    full_address: Mapped[str] = mapped_column(
        "FullAddress",
        Unicode(500),
        nullable = False,
    )
    is_default: Mapped[bool] = mapped_column(
        "IsDefault",
        Boolean,
        nullable = False,
        server_default=text("0"),
    )