import uuid

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    parent_id: uuid.UUID | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


class CategoryTreeNode(CategoryResponse):
    children: list["CategoryTreeNode"] = Field(default_factory=list)

class CategoryUpdate(CategoryCreate):
    pass