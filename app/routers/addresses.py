import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import Address, User
from app.schemas import AddressCreate, AddressResponse, AddressUpdate


router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"],
)


def get_owned_address(
    address_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Address:
    address = db.scalar(
        select(Address).where(
            Address.id == address_id,
            Address.user_id == current_user.id,
        )
    )

    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    return address


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_address_id = db.scalar(
        select(Address.id)
        .where(Address.user_id == current_user.id)
        .limit(1)
    )

    make_default = (
        address_data.is_default or existing_address_id is None
    )

    if make_default:
        db.execute(
            update(Address)
            .where(Address.user_id == current_user.id)
            .values(is_default=False)
        )

    new_address = Address(
        user_id=current_user.id,
        full_name=address_data.full_name,
        phone_number=address_data.phone_number,
        full_address=address_data.full_address,
        is_default=make_default,
    )

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address


@router.get(
    "",
    response_model=list[AddressResponse],
)
def get_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Address)
        .where(Address.user_id == current_user.id)
        .order_by(Address.is_default.desc(), Address.id)
    ).all()


@router.put(
    "/{address_id}",
    response_model=AddressResponse,
)
def update_address(
    address_id: uuid.UUID,
    address_data: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = get_owned_address(address_id, current_user, db)

    address.full_name = address_data.full_name
    address.phone_number = address_data.phone_number
    address.full_address = address_data.full_address

    db.commit()
    db.refresh(address)

    return address


@router.patch(
    "/{address_id}/default",
    response_model=AddressResponse,
)
def set_default_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = get_owned_address(address_id, current_user, db)

    db.execute(
        update(Address)
        .where(Address.user_id == current_user.id)
        .values(is_default=False)
    )

    address.is_default = True

    db.commit()
    db.refresh(address)

    return address


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = get_owned_address(address_id, current_user, db)
    was_default = address.is_default

    db.delete(address)
    db.flush()

    if was_default:
        replacement = db.scalar(
            select(Address)
            .where(Address.user_id == current_user.id)
            .order_by(Address.id)
            .limit(1)
        )

        if replacement is not None:
            replacement.is_default = True

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)