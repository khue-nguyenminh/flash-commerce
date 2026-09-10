import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models import Order, OrderItem, User
from app.schemas import (
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
)


router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin Orders"],
)


def serialize_order(
    order: Order,
    order_items: list[OrderItem],
):
    return {
        "id": order.id,
        "user_id": order.user_id,
        "address_id": order.address_id,
        "coupon_id": order.coupon_id,
        "total_amount": order.total_amount,
        "final_amount": order.final_amount,
        "status": order.status,
        "created_at": order.created_at,
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in order_items
        ],
    }


def get_order_items(
    order_id: uuid.UUID,
    db: Session,
) -> list[OrderItem]:
    return list(
        db.scalars(
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
            .order_by(OrderItem.id)
        ).all()
    )


@router.get(
    "",
    response_model=OrderListResponse,
)
def get_all_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    order_status: str | None = Query(default=None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    allowed_statuses = {
        "Pending",
        "Paid",
        "Processing",
        "Shipped",
        "Completed",
        "Cancelled",
    }

    if (
        order_status is not None
        and order_status not in allowed_statuses
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid order status",
        )

    filters = []

    if order_status is not None:
        filters.append(Order.status == order_status)

    total = (
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(*filters)
        )
        or 0
    )

    orders = db.scalars(
        select(Order)
        .where(*filters)
        .order_by(
            Order.created_at.desc(),
            Order.id,
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    order_ids = [
        order.id
        for order in orders
    ]

    item_map = {
        order_id: []
        for order_id in order_ids
    }

    if order_ids:
        order_items = db.scalars(
            select(OrderItem)
            .where(OrderItem.order_id.in_(order_ids))
            .order_by(OrderItem.id)
        ).all()

        for item in order_items:
            item_map[item.order_id].append(item)

    return {
        "items": [
            serialize_order(
                order,
                item_map[order.id],
            )
            for order in orders
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order_by_admin(
    order_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = db.scalar(
        select(Order).where(Order.id == order_id)
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return serialize_order(
        order,
        get_order_items(order.id, db),
    )


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
def update_order_status(
    order_id: uuid.UUID,
    status_data: OrderStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    allowed_transitions = {
        "Paid": "Processing",
        "Processing": "Shipped",
        "Shipped": "Completed",
    }

    try:
        order = db.scalar(
            select(Order)
            .where(Order.id == order_id)
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

        expected_status = allowed_transitions.get(
            order.status
        )

        if expected_status is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Order in status '{order.status}' "
                    "cannot be updated"
                ),
            )

        if status_data.status != expected_status:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Order must move from '{order.status}' "
                    f"to '{expected_status}'"
                ),
            )

        order.status = status_data.status

        db.commit()
        db.refresh(order)

        order_items = get_order_items(order.id, db)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update order status",
        )

    return serialize_order(
        order,
        order_items,
    )