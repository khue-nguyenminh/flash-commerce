from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import Address, Order, OrderItem, Product, User
from app.schemas import OrderCreate, OrderResponse


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


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