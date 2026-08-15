import random
import string
import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.routers.cart import _compute_summary

router = APIRouter(prefix="/api/orders", tags=["Orders"])


def _generate_order_number():
    return "ORD" + "".join(random.choices(string.digits, k=8))


@router.post("/checkout", response_model=schemas.OrderOut, status_code=201)
def checkout(
    payload: schemas.CheckoutRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Your cart is empty")

    for item in cart_items:
        if item.product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"'{item.product.name}' has insufficient stock")

    coupon = None
    if payload.coupon_code:
        coupon = db.query(models.Coupon).filter(
            models.Coupon.code == payload.coupon_code.upper(), models.Coupon.is_active.is_(True)
        ).first()

    summary = _compute_summary(cart_items, coupon)

    if payload.payment_method not in [m.value for m in models.PaymentMethod]:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    order = models.Order(
        order_number=_generate_order_number(),
        user_id=user.id,
        subtotal=summary["subtotal"],
        discount=summary["discount"],
        delivery_charge=summary["delivery_charge"],
        gst_amount=summary["gst_amount"],
        grand_total=summary["grand_total"],
        coupon_code=payload.coupon_code,
        status=models.OrderStatus.CONFIRMED,
        shipping_name=payload.full_name,
        shipping_phone=payload.phone,
        shipping_address=payload.address_line,
        shipping_city=payload.city,
        shipping_state=payload.state,
        shipping_pincode=payload.pincode,
    )
    db.add(order)
    db.flush()  # get order.id before commit

    for item in cart_items:
        db.add(models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            unit_price=item.product.price,
            quantity=item.quantity,
        ))
        item.product.stock -= item.quantity
        db.delete(item)

    # Demo payment handling. COD stays pending until delivery; online methods are
    # marked paid immediately since this is a demo integration (no live gateway calls).
    payment_status = models.PaymentStatus.PENDING if payload.payment_method == "cod" else models.PaymentStatus.PAID
    db.add(models.Payment(
        order_id=order.id,
        method=payload.payment_method,
        status=payment_status,
        transaction_ref=f"TXN{random.randint(100000, 999999)}",
        amount=summary["grand_total"],
    ))

    db.add(models.Notification(
        user_id=user.id,
        message=f"Order {order.order_number} placed successfully!",
    ))

    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[schemas.OrderOut])
def my_orders(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Order).filter(
        models.Order.user_id == user.id
    ).order_by(models.Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=schemas.OrderOut)
def order_detail(order_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(
        models.Order.id == order_id, models.Order.user_id == user.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}/cancel", response_model=schemas.OrderOut)
def cancel_order(order_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(
        models.Order.id == order_id, models.Order.user_id == user.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in (models.OrderStatus.DELIVERED, models.OrderStatus.CANCELLED):
        raise HTTPException(status_code=400, detail=f"Order cannot be cancelled once {order.status.value}")

    order.status = models.OrderStatus.CANCELLED
    for item in order.items:
        item.product.stock += item.quantity
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/return", response_model=schemas.OrderOut)
def request_return(order_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(
        models.Order.id == order_id, models.Order.user_id == user.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != models.OrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Only delivered orders can be returned")

    order.status = models.OrderStatus.RETURN_REQUESTED
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}/invoice")
def download_invoice(order_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(
        models.Order.id == order_id, models.Order.user_id == user.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    lines = [
        f"INVOICE - {order.order_number}",
        f"Date: {order.created_at.strftime('%d %b %Y')}",
        "-" * 50,
        f"Bill To: {order.shipping_name}",
        f"{order.shipping_address}, {order.shipping_city}, {order.shipping_state} - {order.shipping_pincode}",
        f"Phone: {order.shipping_phone}",
        "-" * 50,
    ]
    for item in order.items:
        lines.append(f"{item.product_name} x{item.quantity} @ Rs.{item.unit_price:.2f} = Rs.{item.unit_price * item.quantity:.2f}")
    lines += [
        "-" * 50,
        f"Subtotal: Rs.{order.subtotal:.2f}",
        f"Discount: -Rs.{order.discount:.2f}",
        f"Delivery: Rs.{order.delivery_charge:.2f}",
        f"GST (18%): Rs.{order.gst_amount:.2f}",
        f"Grand Total: Rs.{order.grand_total:.2f}",
        "-" * 50,
        "Thank you for shopping with ShopAI!",
    ]
    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=invoice_{order.order_number}.txt"},
    )
