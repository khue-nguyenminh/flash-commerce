import uuid
from datetime import datetime
from sqlalchemy import DateTime, Unicode, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class User(Base):
    __tablename__ = "Users"
    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        UNIQUEIDENTIFIER,
        primary_key= True,
        server_default = text("NEWID()"),
    )
    username: Mapped[str] = mapped_column(
        "Username",
        Unicode(50),
        unique = True,
        nullable = False,
    )
    email: Mapped[str] = mapped_column(
        "Email",
        Unicode(100),
        unique = True,
        nullable = False,
    )
    password_hash: Mapped[str] = mapped_column(
        "PasswordHash",
        Unicode(255),
        nullable = False,
    )
    role: Mapped[str] = mapped_column(
        "Role",
        Unicode(20),
        nullable = False,
        server_default = text("'Customer'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime, 
        nullable = False,
        server_default = text("GETUTCDATE()"),
    )