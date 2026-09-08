import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models import Category, Product, ProductCategory, User
from app.schemas import (ProductCreate, ProductResponse, ProductListResponse, ProductUpdate,)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product_data: ProductCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    unique_category_ids = list(dict.fromkeys(product_data.category_ids))

    existing_category_ids = set(
        db.scalars(
            select(Category.id).where(
                Category.id.in_(unique_category_ids)
            )
        ).all()
    )

    missing_category_ids = [
        category_id
        for category_id in unique_category_ids
        if category_id not in existing_category_ids
    ]

    if missing_category_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "One or more categories do not exist",
                "missing_category_ids": [
                    str(category_id)
                    for category_id in missing_category_ids
                ],
            },
        )

    new_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock_quantity=product_data.stock_quantity,
        is_flash_sale=product_data.is_flash_sale,
    )

    db.add(new_product)

    try:
        db.flush()

        for category_id in unique_category_ids:
            db.add(
                ProductCategory(
                    product_id=new_product.id,
                    category_id=category_id,
                )
            )

        db.commit()
        db.refresh(new_product)
    except Exception:
        db.rollback()
        raise

    return {
        "id": new_product.id,
        "name": new_product.name,
        "description": new_product.description,
        "price": new_product.price,
        "stock_quantity": new_product.stock_quantity,
        "is_flash_sale": new_product.is_flash_sale,
        "created_at": new_product.created_at,
        "category_ids": unique_category_ids,
    }

def get_product_or_404(
    product_id: uuid.UUID,
    db: Session,
) -> Product:
    product = db.scalar(
        select(Product).where(Product.id == product_id)
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


def get_product_category_ids(
    product_id: uuid.UUID,
    db: Session,
) -> list[uuid.UUID]:
    return list(
        db.scalars(
            select(ProductCategory.category_id).where(
                ProductCategory.product_id == product_id
            )
        ).all()
    )


@router.get(
    "",
    response_model=ProductListResponse,
)
def get_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    is_flash_sale: bool | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price",
        )

    filters = []

    if search:
        filters.append(Product.name.contains(search))

    if min_price is not None:
        filters.append(Product.price >= min_price)

    if max_price is not None:
        filters.append(Product.price <= max_price)

    if is_flash_sale is not None:
        filters.append(Product.is_flash_sale == is_flash_sale)

    if category_id is not None:
        filters.append(
            Product.id.in_(
                select(ProductCategory.product_id).where(
                    ProductCategory.category_id == category_id
                )
            )
        )

    total = db.scalar(
        select(func.count())
        .select_from(Product)
        .where(*filters)
    )

    products = db.scalars(
        select(Product)
        .where(*filters)
        .order_by(Product.created_at.desc(), Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    product_ids = [product.id for product in products]
    category_map = {
        product_id: []
        for product_id in product_ids
    }

    if product_ids:
        category_rows = db.execute(
            select(
                ProductCategory.product_id,
                ProductCategory.category_id,
            ).where(
                ProductCategory.product_id.in_(product_ids)
            )
        ).all()

        for product_id, product_category_id in category_rows:
            category_map[product_id].append(product_category_id)

    items = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock_quantity": product.stock_quantity,
            "is_flash_sale": product.is_flash_sale,
            "created_at": product.created_at,
            "category_ids": category_map[product.id],
        }
        for product in products
    ]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    product = get_product_or_404(product_id, db)

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "is_flash_sale": product.is_flash_sale,
        "created_at": product.created_at,
        "category_ids": get_product_category_ids(product.id, db),
    }


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: uuid.UUID,
    product_data: ProductUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = get_product_or_404(product_id, db)
    unique_category_ids = list(dict.fromkeys(product_data.category_ids))

    existing_category_ids = set(
        db.scalars(
            select(Category.id).where(
                Category.id.in_(unique_category_ids)
            )
        ).all()
    )

    missing_category_ids = [
        category_id
        for category_id in unique_category_ids
        if category_id not in existing_category_ids
    ]

    if missing_category_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "One or more categories do not exist",
                "missing_category_ids": [
                    str(category_id)
                    for category_id in missing_category_ids
                ],
            },
        )

    product.name = product_data.name
    product.description = product_data.description
    product.price = product_data.price
    product.stock_quantity = product_data.stock_quantity
    product.is_flash_sale = product_data.is_flash_sale

    try:
        db.execute(
            delete(ProductCategory).where(
                ProductCategory.product_id == product_id
            )
        )

        for category_id in unique_category_ids:
            db.add(
                ProductCategory(
                    product_id=product_id,
                    category_id=category_id,
                )
            )

        db.commit()
        db.refresh(product)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update product",
        )

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "is_flash_sale": product.is_flash_sale,
        "created_at": product.created_at,
        "category_ids": unique_category_ids,
    }


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = get_product_or_404(product_id, db)

    try:
        db.execute(
            delete(ProductCategory).where(
                ProductCategory.product_id == product_id
            )
        )
        db.delete(product)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete product because it is already in use",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)