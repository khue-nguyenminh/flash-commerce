import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    product_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewUpdate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    rating: int
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)