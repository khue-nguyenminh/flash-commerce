import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models import Coupon, User
from app.schemas import CouponCreate, CouponResponse, CouponUpdate


router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"],
)


def get_coupon_or_404(
    coupon_id: uuid.UUID,
    db: Session,
) -> Coupon:
    coupon = db.scalar(
        select(Coupon).where(Coupon.id == coupon_id)
    )

    if coupon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found",
        )

    return coupon


@router.post(
    "",
    response_model=CouponResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_coupon(
    coupon_data: CouponCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing_coupon = db.scalar(
        select(Coupon).where(
            Coupon.code == coupon_data.code
        )
    )

    if existing_coupon is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Coupon code already exists",
        )

    coupon = Coupon(
        code=coupon_data.code,
        discount_percent=coupon_data.discount_percent,
        max_usage=coupon_data.max_usage,
        current_usage=0,
        valid_from=coupon_data.valid_from,
        valid_to=coupon_data.valid_to,
    )

    db.add(coupon)

    try:
        db.commit()
        db.refresh(coupon)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Coupon code already exists",
        )

    return coupon


@router.get(
    "",
    response_model=list[CouponResponse],
)
def get_coupons(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Coupon)
        .order_by(Coupon.valid_to.desc(), Coupon.id)
    ).all()


@router.get(
    "/{coupon_id}",
    response_model=CouponResponse,
)
def get_coupon(
    coupon_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_coupon_or_404(coupon_id, db)


@router.put(
    "/{coupon_id}",
    response_model=CouponResponse,
)
def update_coupon(
    coupon_id: uuid.UUID,
    coupon_data: CouponUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    coupon = get_coupon_or_404(coupon_id, db)

    duplicate_coupon = db.scalar(
        select(Coupon).where(
            Coupon.code == coupon_data.code,
            Coupon.id != coupon_id,
        )
    )

    if duplicate_coupon is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Coupon code already exists",
        )

    if coupon_data.max_usage < coupon.current_usage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "max_usage cannot be lower than current_usage"
            ),
        )

    coupon.code = coupon_data.code
    coupon.discount_percent = coupon_data.discount_percent
    coupon.max_usage = coupon_data.max_usage
    coupon.valid_from = coupon_data.valid_from
    coupon.valid_to = coupon_data.valid_to

    try:
        db.commit()
        db.refresh(coupon)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Coupon code already exists",
        )

    return coupon


@router.delete(
    "/{coupon_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_coupon(
    coupon_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    coupon = get_coupon_or_404(coupon_id, db)

    try:
        db.delete(coupon)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete coupon because it is already in use",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)