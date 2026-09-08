import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.models import Address, Order, OrderItem, Product, User
from app.schemas import OrderCreate, OrderResponse, OrderListResponse

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)

def serialize_order(
    order: Order,
    order_items: list[OrderItem],
):
    return {
        "id": order.id,
        "user_id": order.user_id,
        "address_id": order.address_id,
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

@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        address = db.scalar(
            select(Address).where(
                Address.id == order_data.address_id,
                Address.user_id == current_user.id,
            )
        )

        if address is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found",
            )

        requested_items = {
            item.product_id: item.quantity
            for item in order_data.items
        }

        # Sort IDs so concurrent orders lock products in the same order.
        # This reduces the chance of database deadlocks.
        sorted_product_ids = sorted(
            requested_items,
            key=str,
        )

        locked_products = {}

        for product_id in sorted_product_ids:
            product = db.scalar(
                select(Product)
                .where(Product.id == product_id)
                .with_hint(
                    Product,
                    "WITH (UPDLOCK, ROWLOCK)",
                    dialect_name="mssql",
                )
            )

            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {product_id} not found",
                )

            requested_quantity = requested_items[product_id]

            if product.stock_quantity < requested_quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": "Insufficient stock",
                        "product_id": str(product.id),
                        "requested_quantity": requested_quantity,
                        "available_quantity": product.stock_quantity,
                    },
                )

            locked_products[product_id] = product

        total_amount = sum(
            (
                locked_products[product_id].price
                * requested_items[product_id]
                for product_id in sorted_product_ids
            ),
            Decimal("0.00"),
        )

        new_order = Order(
            user_id=current_user.id,
            address_id=address.id,
            coupon_id=None,
            total_amount=total_amount,
            final_amount=total_amount,
            status="Pending",
        )

        db.add(new_order)
        db.flush()

        response_items = []

        for product_id in sorted_product_ids:
            product = locked_products[product_id]
            quantity = requested_items[product_id]

            product.stock_quantity -= quantity

            db.add(
                OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )

            response_items.append(
                {
                    "product_id": product.id,
                    "quantity": quantity,
                    "unit_price": product.price,
                }
            )

        db.commit()
        db.refresh(new_order)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create order",
        )

    return {
        "id": new_order.id,
        "user_id": new_order.user_id,
        "address_id": new_order.address_id,
        "total_amount": new_order.total_amount,
        "final_amount": new_order.final_amount,
        "status": new_order.status,
        "created_at": new_order.created_at,
        "items": response_items,
    }

@router.get(
    "",
    response_model=OrderListResponse,
)
def get_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = (
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.user_id == current_user.id)
        )
        or 0
    )

    orders = db.scalars(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc(), Order.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    order_ids = [order.id for order in orders]

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

        for order_item in order_items:
            item_map[order_item.order_id].append(order_item)

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
def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.scalar(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    order_items = db.scalars(
        select(OrderItem)
        .where(OrderItem.order_id == order.id)
        .order_by(OrderItem.id)
    ).all()

    return serialize_order(order, order_items)


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Lock the Order so two cancellation requests cannot both refund stock.
        order = db.scalar(
            select(Order)
            .where(
                Order.id == order_id,
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
                detail=(
                    "Only Pending orders can be cancelled"
                ),
            )

        order_items = db.scalars(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .order_by(OrderItem.product_id)
        ).all()

        item_by_product_id = {
            item.product_id: item
            for item in order_items
        }

        sorted_product_ids = sorted(
            item_by_product_id,
            key=str,
        )

        # Lock Product rows before restoring stock.
        for product_id in sorted_product_ids:
            product = db.scalar(
                select(Product)
                .where(Product.id == product_id)
                .with_hint(
                    Product,
                    "WITH (UPDLOCK, ROWLOCK)",
                    dialect_name="mssql",
                )
            )

            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Product {product_id} no longer exists"
                    ),
                )

            product.stock_quantity += (
                item_by_product_id[product_id].quantity
            )

        order.status = "Cancelled"

        db.commit()
        db.refresh(order)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to cancel order",
        )

    return serialize_order(order, order_items)