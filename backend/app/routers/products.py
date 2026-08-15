from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_optional_user

router = APIRouter(prefix="/api/products", tags=["Products"])


def _slugify(name: str) -> str:
    return "-".join(name.lower().split())


@router.get("", response_model=list[schemas.ProductListItem])
def list_products(
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock_only: bool = False,
    sort_by: str = Query("newest", pattern="^(newest|price_low|price_high|rating|popularity)$"),
    featured: Optional[bool] = None,
    best_seller: Optional[bool] = None,
    trending: Optional[bool] = None,
    flash_sale: Optional[bool] = None,
    limit: int = Query(24, le=100),
    offset: int = 0,
):
    q = db.query(models.Product).filter(models.Product.is_active.is_(True))

    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.Product.name.ilike(like), models.Product.brand.ilike(like)))
    if category_id:
        q = q.filter(models.Product.category_id == category_id)
    if brand:
        q = q.filter(models.Product.brand == brand)
    if min_price is not None:
        q = q.filter(models.Product.price >= min_price)
    if max_price is not None:
        q = q.filter(models.Product.price <= max_price)
    if min_rating is not None:
        q = q.filter(models.Product.rating_avg >= min_rating)
    if in_stock_only:
        q = q.filter(models.Product.stock > 0)
    if featured:
        q = q.filter(models.Product.is_featured.is_(True))
    if best_seller:
        q = q.filter(models.Product.is_best_seller.is_(True))
    if trending:
        q = q.filter(models.Product.is_trending.is_(True))
    if flash_sale:
        q = q.filter(models.Product.is_flash_sale.is_(True))

    if sort_by == "price_low":
        q = q.order_by(models.Product.price.asc())
    elif sort_by == "price_high":
        q = q.order_by(models.Product.price.desc())
    elif sort_by == "rating":
        q = q.order_by(models.Product.rating_avg.desc())
    elif sort_by == "popularity":
        q = q.order_by(models.Product.rating_count.desc())
    else:
        q = q.order_by(models.Product.created_at.desc())

    return q.offset(offset).limit(limit).all()


@router.get("/brands")
def list_brands(db: Session = Depends(get_db)):
    rows = db.query(models.Product.brand).filter(
        models.Product.brand.isnot(None), models.Product.is_active.is_(True)
    ).distinct().all()
    return sorted({r[0] for r in rows if r[0]})


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_optional_user),
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id, models.Product.is_active.is_(True)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if user:
        existing = db.query(models.RecentlyViewed).filter(
            models.RecentlyViewed.user_id == user.id,
            models.RecentlyViewed.product_id == product_id,
        ).first()
        if existing:
            existing.viewed_at = models.now()
        else:
            db.add(models.RecentlyViewed(user_id=user.id, product_id=product_id))
        db.commit()

    return product


@router.get("/{product_id}/similar", response_model=list[schemas.ProductListItem])
def similar_products(product_id: int, db: Session = Depends(get_db), limit: int = 8):
    from app.services.recommendation import get_similar_products
    ids = get_similar_products(db, product_id, top_n=limit)
    if not ids:
        return []
    products = db.query(models.Product).filter(models.Product.id.in_(ids)).all()
    order = {pid: i for i, pid in enumerate(ids)}
    return sorted(products, key=lambda p: order.get(p.id, 999))


@router.get("/{product_id}/reviews", response_model=list[schemas.ReviewOut])
def product_reviews(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.Review).filter(
        models.Review.product_id == product_id
    ).order_by(models.Review.created_at.desc()).all()


# ---- Categories ----

categories_router = APIRouter(prefix="/api/categories", tags=["Categories"])


@categories_router.get("", response_model=list[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()
