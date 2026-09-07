import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(
        min_length = 3,
        max_length = 50,
        pattern = r"^[A-Za-z0-9_.-]+$",
    )
    email: EmailStr
    password: str = Field(min_length=8, max_length = 128)

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes = True)