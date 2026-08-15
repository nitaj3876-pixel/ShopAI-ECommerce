from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


def _recalculate_rating(db: Session, product_id: int):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    reviews = db.query(models.Review).filter(models.Review.product_id == product_id).all()
    if reviews:
        product.rating_avg = round(sum(r.rating for r in reviews) / len(reviews), 1)
        product.rating_count = len(reviews)
    else:
        product.rating_avg = 0
        product.rating_count = 0
    db.commit()


@router.post("", response_model=schemas.ReviewOut, status_code=201)
def create_review(
    payload: schemas.ReviewCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(models.Review).filter(
        models.Review.user_id == user.id, models.Review.product_id == payload.product_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You've already reviewed this product")

    review = models.Review(user_id=user.id, **payload.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)

    _recalculate_rating(db, payload.product_id)
    return review


@router.delete("/{review_id}")
def delete_review(review_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(
        models.Review.id == review_id, models.Review.user_id == user.id
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    product_id = review.product_id
    db.delete(review)
    db.commit()
    _recalculate_rating(db, product_id)
    return {"message": "Review deleted"}
