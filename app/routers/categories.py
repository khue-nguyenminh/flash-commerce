import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models import Category, ProductCategory, User
from app.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeNode,
    CategoryUpdate,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.get(
    "/tree",
    response_model=list[CategoryTreeNode],
)
def get_category_tree(
    db: Session = Depends(get_db),
):
    query = text(
        """
        WITH CategoryTree AS (
            SELECT
                Id,
                Name,
                ParentId,
                Slug,
                0 AS Depth
            FROM Categories
            WHERE ParentId IS NULL

            UNION ALL

            SELECT
                child.Id,
                child.Name,
                child.ParentId,
                child.Slug,
                parent.Depth + 1
            FROM Categories AS child
            INNER JOIN CategoryTree AS parent
                ON child.ParentId = parent.Id
        )
        SELECT
            Id AS id,
            Name AS name,
            ParentId AS parent_id,
            Slug AS slug,
            Depth AS depth
        FROM CategoryTree
        ORDER BY Depth, Name
        OPTION (MAXRECURSION 100)
        """
    )

    rows = db.execute(query).mappings().all()

    nodes = {}
    roots = []

    for row in rows:
        node_id = str(row["id"])

        nodes[node_id] = {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "parent_id": row["parent_id"],
            "children": [],
        }

    for row in rows:
        node = nodes[str(row["id"])]
        parent_id = row["parent_id"]

        if parent_id is None:
            roots.append(node)
        else:
            parent = nodes.get(str(parent_id))

            if parent is not None:
                parent["children"].append(node)

    return roots


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    category_data: CategoryCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing_slug = db.scalar(
        select(Category).where(
            Category.slug == category_data.slug
        )
    )

    if existing_slug is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category slug already exists",
        )

    if category_data.parent_id is not None:
        parent = db.scalar(
            select(Category).where(
                Category.id == category_data.parent_id
            )
        )

        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category does not exist",
            )

    new_category = Category(
        name=category_data.name,
        slug=category_data.slug,
        parent_id=category_data.parent_id,
    )

    db.add(new_category)

    try:
        db.commit()
        db.refresh(new_category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category slug already exists",
        )

    return new_category

def get_category_or_404(
    category_id: uuid.UUID,
    db: Session,
) -> Category:
    category = db.scalar(
        select(Category).where(Category.id == category_id)
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return get_category_or_404(category_id, db)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category(
    category_id: uuid.UUID,
    category_data: CategoryUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    category = get_category_or_404(category_id, db)

    duplicate_slug = db.scalar(
        select(Category).where(
            Category.slug == category_data.slug,
            Category.id != category_id,
        )
    )

    if duplicate_slug is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category slug already exists",
        )

    if category_data.parent_id == category_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot be its own parent",
        )

    if category_data.parent_id is not None:
        parent = db.scalar(
            select(Category).where(
                Category.id == category_data.parent_id
            )
        )

        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category does not exist",
            )

        descendant_count = db.scalar(
            text(
                """
                WITH Descendants AS (
                    SELECT Id
                    FROM Categories
                    WHERE ParentId = :category_id

                    UNION ALL

                    SELECT child.Id
                    FROM Categories AS child
                    INNER JOIN Descendants AS parent
                        ON child.ParentId = parent.Id
                )
                SELECT COUNT(*)
                FROM Descendants
                WHERE Id = :parent_id
                OPTION (MAXRECURSION 100)
                """
            ),
            {
                "category_id": category_id,
                "parent_id": category_data.parent_id,
            },
        )

        if descendant_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move category under its descendant",
            )

    category.name = category_data.name
    category.slug = category_data.slug
    category.parent_id = category_data.parent_id

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category slug already exists",
        )

    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    category = get_category_or_404(category_id, db)

    child_id = db.scalar(
        select(Category.id)
        .where(Category.parent_id == category_id)
        .limit(1)
    )

    if child_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete category that has child categories",
        )

    linked_product_id = db.scalar(
        select(ProductCategory.product_id)
        .where(ProductCategory.category_id == category_id)
        .limit(1)
    )

    if linked_product_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete category linked to products",
        )

    db.delete(category)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)