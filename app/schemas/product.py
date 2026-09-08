import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0, decimal_places=2)
    stock_quantity: int = Field(ge=0)
    is_flash_sale: bool = False
    category_ids: list[uuid.UUID] = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int
    is_flash_sale: bool
    created_at: datetime
    category_ids: list[uuid.UUID]

class ProductUpdate(ProductCreate):
    pass

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    page: int
    page_size: int
    total: int