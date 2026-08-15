import os
import re
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])
UPLOAD_DIRECTORY = Path("uploads/products")
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "product"


def _unique_slug(db: Session, name: str, excluding_product_id: Optional[int] = None) -> str:
    base_slug = _slugify(name)
    slug, suffix = base_slug, 1
    while True:
        query = db.query(models.Product).filter(models.Product.slug == slug)
        if excluding_product_id is not None:
            query = query.filter(models.Product.id != excluding_product_id)
        if not query.first():
            return slug
        suffix += 1
        slug = f"{base_slug}-{suffix}"


def _validate_category(db: Session, category_id: int) -> None:
    if not db.query(models.Category).filter(models.Category.id == category_id).first():
        raise HTTPException(status_code=400, detail="Selected category does not exist")


def _image_extension(image: UploadFile, contents: bytes) -> str:
    signatures = {
        b"\xff\xd8\xff": ".jpg",
        b"\x89PNG\r\n\x1a\n": ".png",
        b"GIF87a": ".gif",
        b"GIF89a": ".gif",
        b"RIFF": ".webp",
    }
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, WebP and GIF images are allowed")
    for signature, extension in signatures.items():
        if contents.startswith(signature):
            if extension == ".webp" and contents[8:12] != b"WEBP":
                break
            return extension
    raise HTTPException(status_code=400, detail="The uploaded file is not a valid image")


# ---------- Dashboard ----------

@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    total_revenue = db.query(func.sum(models.Order.grand_total)).filter(
        models.Order.status != models.OrderStatus.CANCELLED
    ).scalar() or 0
    return schemas.DashboardStats(
        total_users=db.query(models.User).filter(models.User.is_admin.is_(False)).count(),
        total_products=db.query(models.Product).count(),
        total_orders=db.query(models.Order).count(),
        total_revenue=round(total_revenue, 2),
        pending_orders=db.query(models.Order).filter(
            models.Order.status.in_([models.OrderStatus.PENDING, models.OrderStatus.CONFIRMED])
        ).count(),
        total_categories=db.query(models.Category).count(),
        total_stock=db.query(func.coalesce(func.sum(models.Product.stock), 0)).filter(
            models.Product.is_active.is_(True)
        ).scalar() or 0,
        low_stock_products=db.query(models.Product).filter(
            models.Product.is_active.is_(True), models.Product.stock.between(1, 10)
        ).count(),
        out_of_stock_products=db.query(models.Product).filter(
            models.Product.is_active.is_(True), models.Product.stock == 0
        ).count(),
    )


@router.get("/analytics/monthly-sales")
def monthly_sales(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    orders = db.query(models.Order).filter(models.Order.status != models.OrderStatus.CANCELLED).all()
    buckets: dict[str, float] = {}
    for o in orders:
        key = o.created_at.strftime("%Y-%m")
        buckets[key] = buckets.get(key, 0) + o.grand_total
    return [{"month": k, "revenue": round(v, 2)} for k, v in sorted(buckets.items())]


@router.get("/analytics/daily-orders")
def daily_orders(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    orders = db.query(models.Order).all()
    buckets: dict[str, int] = {}
    for o in orders:
        key = o.created_at.strftime("%Y-%m-%d")
        buckets[key] = buckets.get(key, 0) + 1
    return [{"date": k, "orders": v} for k, v in sorted(buckets.items())][-30:]


@router.get("/analytics/top-products")
def top_products(db: Session = Depends(get_db), _admin=Depends(get_current_admin), limit: int = 10):
    rows = db.query(
        models.OrderItem.product_name,
        func.sum(models.OrderItem.quantity).label("units_sold"),
    ).group_by(models.OrderItem.product_name).order_by(func.sum(models.OrderItem.quantity).desc()).limit(limit).all()
    return [{"product_name": r[0], "units_sold": int(r[1])} for r in rows]


@router.get("/analytics/category-sales")
def category_sales(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    rows = db.query(
        models.Category.name,
        func.sum(models.OrderItem.quantity * models.OrderItem.unit_price).label("revenue"),
    ).join(models.Product, models.Product.category_id == models.Category.id).join(
        models.OrderItem, models.OrderItem.product_id == models.Product.id
    ).group_by(models.Category.name).all()
    return [{"category": r[0], "revenue": round(r[1] or 0, 2)} for r in rows]


# ---------- Products ----------

@router.get("/products", response_model=list[schemas.ProductOut])
def admin_list_products(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    stock_status: str = Query("all", pattern="^(all|in_stock|low_stock|out_of_stock|archived)$"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(models.Product)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(models.Product.name.ilike(like), models.Product.brand.ilike(like)))
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if stock_status == "archived":
        query = query.filter(models.Product.is_active.is_(False))
    else:
        query = query.filter(models.Product.is_active.is_(True))
        if stock_status == "in_stock":
            query = query.filter(models.Product.stock > 10)
        elif stock_status == "low_stock":
            query = query.filter(models.Product.stock.between(1, 10))
        elif stock_status == "out_of_stock":
            query = query.filter(models.Product.stock == 0)
    return query.order_by(models.Product.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/products", response_model=schemas.ProductOut, status_code=201)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    _validate_category(db, payload.category_id)
    slug = _unique_slug(db, payload.name)

    product = models.Product(**payload.model_dump(), slug=slug)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    changes = payload.model_dump(exclude_unset=True)
    if "category_id" in changes:
        _validate_category(db, changes["category_id"])
    if "name" in changes and changes["name"] != product.name:
        product.slug = _unique_slug(db, changes["name"], product.id)
    for field, value in changes.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Preserve references held by orders, carts and wishlists. Archived products
    # no longer appear in the customer catalog but remain auditable to admins.
    product.is_active = False
    db.commit()
    return {"message": "Product archived"}


@router.post("/products/upload-image")
async def upload_product_image(
    image: UploadFile = File(...), _admin=Depends(get_current_admin)
):
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Choose an image to upload")
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Image must be 5 MB or smaller")
    extension = _image_extension(image, contents)
    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    (UPLOAD_DIRECTORY / filename).write_bytes(contents)
    return {"image_url": f"/uploads/products/{filename}"}


# ---------- Categories ----------

@router.post("/categories", response_model=schemas.CategoryOut, status_code=201)
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    slug = _slugify(payload.name)
    if db.query(models.Category).filter(models.Category.slug == slug).first():
        raise HTTPException(status_code=400, detail="Category already exists")
    category = models.Category(name=payload.name, slug=slug, image_url=payload.image_url)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}


# ---------- Users ----------

@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return db.query(models.User).filter(models.User.is_admin.is_(False)).all()


@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User is now {'active' if user.is_active else 'disabled'}"}


# ---------- Orders ----------

@router.get("/orders", response_model=list[schemas.OrderOut])
def list_all_orders(db: Session = Depends(get_db), _admin=Depends(get_current_admin), status: str | None = None):
    q = db.query(models.Order)
    if status:
        q = q.filter(models.Order.status == status)
    return q.order_by(models.Order.created_at.desc()).all()


@router.put("/orders/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(order_id: int, payload: schemas.OrderStatusUpdate, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    valid_statuses = [s.value for s in models.OrderStatus]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order


# ---------- Reviews ----------

@router.get("/reviews", response_model=list[schemas.ReviewOut])
def list_all_reviews(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return db.query(models.Review).order_by(models.Review.created_at.desc()).all()


@router.delete("/reviews/{review_id}")
def admin_delete_review(review_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
    return {"message": "Review deleted"}


# ---------- Coupons ----------

@router.get("/coupons", response_model=list[schemas.CouponOut])
def list_coupons(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return db.query(models.Coupon).all()


@router.post("/coupons", response_model=schemas.CouponOut, status_code=201)
def create_coupon(payload: schemas.CouponCreate, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    if db.query(models.Coupon).filter(models.Coupon.code == payload.code.upper()).first():
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    coupon = models.Coupon(**{**payload.model_dump(), "code": payload.code.upper()})
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/coupons/{coupon_id}")
def delete_coupon(coupon_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    coupon = db.query(models.Coupon).filter(models.Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db.delete(coupon)
    db.commit()
    return {"message": "Coupon deleted"}
