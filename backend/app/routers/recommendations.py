from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.services import recommendation as rec

router = APIRouter(prefix="/api/recommendations", tags=["AI Recommendations"])


def _to_products(db, ids):
    if not ids:
        return []
    products = db.query(models.Product).filter(models.Product.id.in_(ids)).all()
    order = {pid: i for i, pid in enumerate(ids)}
    return sorted(products, key=lambda p: order.get(p.id, 999))


@router.get("/similar/{product_id}", response_model=list[schemas.ProductListItem])
def similar(product_id: int, db: Session = Depends(get_db), limit: int = 8):
    return _to_products(db, rec.get_similar_products(db, product_id, limit))


@router.get("/frequently-bought-together/{product_id}", response_model=list[schemas.ProductListItem])
def fbt(product_id: int, db: Session = Depends(get_db), limit: int = 4):
    return _to_products(db, rec.get_frequently_bought_together(db, product_id, limit))


@router.get("/personalized", response_model=list[schemas.ProductListItem])
def personalized(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 12,
):
    return _to_products(db, rec.get_personalized_recommendations(db, user.id, limit))


@router.get("/recently-viewed", response_model=list[schemas.ProductListItem])
def recently_viewed(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
):
    rows = db.query(models.RecentlyViewed).filter(
        models.RecentlyViewed.user_id == user.id
    ).order_by(models.RecentlyViewed.viewed_at.desc()).limit(limit).all()
    ids = [r.product_id for r in rows]
    return _to_products(db, ids)
