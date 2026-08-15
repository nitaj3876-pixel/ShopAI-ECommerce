from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


@router.get("", response_model=list[schemas.WishlistItemOut])
def get_wishlist(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.WishlistItem).filter(models.WishlistItem.user_id == user.id).all()


@router.post("/{product_id}", status_code=201)
def add_to_wishlist(product_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == user.id, models.WishlistItem.product_id == product_id
    ).first()
    if existing:
        return {"message": "Already in wishlist"}

    db.add(models.WishlistItem(user_id=user.id, product_id=product_id))
    db.commit()
    return {"message": "Added to wishlist"}


@router.delete("/{product_id}")
def remove_from_wishlist(product_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == user.id, models.WishlistItem.product_id == product_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in wishlist")
    db.delete(item)
    db.commit()
    return {"message": "Removed from wishlist"}


@router.post("/{product_id}/move-to-cart")
def move_to_cart(product_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == user.id, models.WishlistItem.product_id == product_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in wishlist")

    cart_item = db.query(models.CartItem).filter(
        models.CartItem.user_id == user.id, models.CartItem.product_id == product_id
    ).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        db.add(models.CartItem(user_id=user.id, product_id=product_id, quantity=1))

    db.delete(item)
    db.commit()
    return {"message": "Moved to cart"}
