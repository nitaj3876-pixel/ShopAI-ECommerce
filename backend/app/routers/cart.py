from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/api/cart", tags=["Cart"])

DELIVERY_CHARGE = 49.0
FREE_DELIVERY_THRESHOLD = 999.0
GST_RATE = 0.18


def _compute_summary(items: list[models.CartItem], coupon: models.Coupon | None = None):
    subtotal = sum(i.product.price * i.quantity for i in items)
    discount = 0.0
    if coupon and subtotal >= coupon.min_order_value:
        discount = subtotal * (coupon.discount_percent / 100)
    taxable = subtotal - discount
    gst_amount = round(taxable * GST_RATE, 2)
    delivery_charge = 0.0 if subtotal >= FREE_DELIVERY_THRESHOLD or subtotal == 0 else DELIVERY_CHARGE
    grand_total = round(taxable + gst_amount + delivery_charge, 2)
    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "delivery_charge": delivery_charge,
        "gst_amount": gst_amount,
        "grand_total": grand_total,
    }


@router.get("", response_model=schemas.CartSummary)
def get_cart(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    summary = _compute_summary(items)
    return schemas.CartSummary(items=items, **summary)


@router.post("/items", response_model=schemas.CartSummary, status_code=201)
def add_to_cart(
    payload: schemas.CartItemCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < payload.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    item = db.query(models.CartItem).filter(
        models.CartItem.user_id == user.id, models.CartItem.product_id == payload.product_id
    ).first()
    if item:
        item.quantity += payload.quantity
    else:
        item = models.CartItem(user_id=user.id, product_id=payload.product_id, quantity=payload.quantity)
        db.add(item)
    db.commit()

    items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    return schemas.CartSummary(items=items, **_compute_summary(items))


@router.put("/items/{item_id}", response_model=schemas.CartSummary)
def update_cart_item(
    item_id: int,
    payload: schemas.CartItemUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id, models.CartItem.user_id == user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    item.quantity = payload.quantity
    db.commit()

    items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    return schemas.CartSummary(items=items, **_compute_summary(items))


@router.delete("/items/{item_id}", response_model=schemas.CartSummary)
def remove_cart_item(item_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id, models.CartItem.user_id == user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()

    items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    return schemas.CartSummary(items=items, **_compute_summary(items))


@router.post("/apply-coupon", response_model=schemas.CartSummary)
def apply_coupon(code: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    coupon = db.query(models.Coupon).filter(
        models.Coupon.code == code.upper(), models.Coupon.is_active.is_(True)
    ).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid or expired coupon code")

    items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    summary = _compute_summary(items, coupon)
    if summary["discount"] == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Add items worth ₹{coupon.min_order_value:.0f} or more to use this coupon",
        )
    return schemas.CartSummary(items=items, **summary)
