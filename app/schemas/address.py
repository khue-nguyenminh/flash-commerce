import uuid

from pydantic import BaseModel, ConfigDict, Field


class AddressBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    phone_number: str = Field(min_length=8, max_length=20)
    full_address: str = Field(min_length=5, max_length=500)

    model_config = ConfigDict(str_strip_whitespace=True)


class AddressCreate(AddressBase):
    is_default: bool = False


class AddressUpdate(AddressBase):
    pass


class AddressResponse(AddressBase):
    id: uuid.UUID
    is_default: bool

    model_config = ConfigDict(from_attributes=True)