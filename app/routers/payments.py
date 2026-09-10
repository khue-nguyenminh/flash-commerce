import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import Order, Payment, User
from app.schemas import PaymentCreate, PaymentResponse


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Khóa Order để hai request không thể cùng thanh toán.
        order = db.scalar(
            select(Order)
            .where(
                Order.id == payment_data.order_id,
                Order.user_id == current_user.id,
            )
            .with_hint(
                Order,
                "WITH (UPDLOCK, ROWLOCK)",
                dialect_name="mssql",
            )
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        if order.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only Pending orders can be paid",
            )

        existing_payment = db.scalar(
            select(Payment).where(
                Payment.order_id == order.id
            )
        )

        if existing_payment is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order already has a payment",
            )

        payment = Payment(
            order_id=order.id,
            payment_method=payment_data.payment_method,
            transaction_id=str(uuid.uuid4()),
            amount=order.final_amount,
            status="Completed",
        )

        order.status = "Paid"

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process payment",
        )


@router.get(
    "/order/{order_id}",
    response_model=PaymentResponse,
)
def get_payment_by_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.scalar(
        select(Payment)
        .join(Order, Payment.order_id == Order.id)
        .where(
            Payment.order_id == order_id,
            Order.user_id == current_user.id,
        )
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return payment