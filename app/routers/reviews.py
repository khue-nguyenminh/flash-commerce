import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import (
    Order,
    OrderItem,
    Product,
    Review,
    User,
)
from app.schemas import (
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


def get_owned_review_or_404(
    review_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session,
) -> Review:
    review = db.scalar(
        select(Review).where(
            Review.id == review_id,
            Review.user_id == user_id,
        )
    )

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return review


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.scalar(
        select(Product).where(
            Product.id == review_data.product_id
        )
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    completed_purchase = db.scalar(
        select(OrderItem.id)
        .join(
            Order,
            OrderItem.order_id == Order.id,
        )
        .where(
            Order.user_id == current_user.id,
            OrderItem.product_id == review_data.product_id,
            Order.status == "Completed",
        )
        .limit(1)
    )

    if completed_purchase is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only customers who completed an order "
                "containing this product can review it"
            ),
        )

    existing_review = db.scalar(
        select(Review).where(
            Review.user_id == current_user.id,
            Review.product_id == review_data.product_id,
        )
    )

    if existing_review is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product",
        )

    review = Review(
        user_id=current_user.id,
        product_id=review_data.product_id,
        rating=review_data.rating,
        comment=review_data.comment,
    )

    db.add(review)

    try:
        db.commit()
        db.refresh(review)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product",
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create review",
        )

    return review


@router.get(
    "/product/{product_id}",
    response_model=list[ReviewResponse],
)
def get_product_reviews(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    product = db.scalar(
        select(Product).where(Product.id == product_id)
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return db.scalars(
        select(Review)
        .where(Review.product_id == product_id)
        .order_by(
            Review.created_at.desc(),
            Review.id,
        )
    ).all()


@router.get(
    "/me",
    response_model=list[ReviewResponse],
)
def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Review)
        .where(Review.user_id == current_user.id)
        .order_by(
            Review.created_at.desc(),
            Review.id,
        )
    ).all()


@router.put(
    "/{review_id}",
    response_model=ReviewResponse,
)
def update_review(
    review_id: uuid.UUID,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = get_owned_review_or_404(
        review_id,
        current_user.id,
        db,
    )

    review.rating = review_data.rating
    review.comment = review_data.comment

    try:
        db.commit()
        db.refresh(review)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update review",
        )

    return review


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = get_owned_review_or_404(
        review_id,
        current_user.id,
        db,
    )

    try:
        db.delete(review)
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete review",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )