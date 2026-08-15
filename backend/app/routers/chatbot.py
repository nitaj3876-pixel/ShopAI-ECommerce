"""
AI Shopping Assistant.

Uses lightweight intent-matching (keyword rules) rather than a full LLM call so the
project runs completely offline with zero external API keys. The intent layer is
isolated in `detect_intent`, so it can be swapped for a real LLM call later by
replacing that one function with a prompt to an API such as the Anthropic API.
"""
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/chatbot", tags=["AI Chatbot"])

FAQ_ANSWERS = {
    "return": "You can return any delivered item within 7 days from your Orders page — just click 'Return Request' on the order.",
    "refund": "Refunds are processed within 5-7 business days to your original payment method once we receive the returned item.",
    "shipping": "Standard delivery takes 3-5 business days. Orders above ₹999 get free delivery!",
    "delivery": "Standard delivery takes 3-5 business days. Orders above ₹999 get free delivery!",
    "payment": "We accept Cash on Delivery, UPI, Razorpay, and Stripe (cards/net-banking).",
    "cancel": "You can cancel any order that hasn't shipped yet from the Orders page.",
    "track": "Head to 'My Orders' and click any order to see its live status and tracking timeline.",
}


def detect_intent(message: str) -> str:
    m = message.lower()
    if any(w in m for w in ["hi", "hello", "hey"]) and len(m.split()) <= 3:
        return "greeting"
    if any(w in m for w in ["track", "where is my order", "order status"]):
        return "track"
    if any(w in m for w in ["return", "refund"]):
        return "return" if "refund" not in m else "refund"
    if any(w in m for w in ["cancel"]):
        return "cancel"
    if any(w in m for w in ["ship", "delivery", "deliver"]):
        return "shipping"
    if any(w in m for w in ["pay", "payment", "upi", "cod", "card"]):
        return "payment"
    if any(w in m for w in ["checkout", "buy", "order now", "place order"]):
        return "checkout_help"
    if any(w in m for w in ["find", "search", "show", "looking for", "suggest", "recommend", "need"]):
        return "product_search"
    return "product_search"  # default: try to help find a product


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    intent = detect_intent(payload.message)

    if intent == "greeting":
        return schemas.ChatResponse(
            reply="Hi! 👋 I'm your ShopAI assistant. I can help you find products, track orders, or answer questions about returns, shipping and payments. What are you looking for today?"
        )

    if intent == "checkout_help":
        return schemas.ChatResponse(
            reply="To checkout: open your Cart, apply any coupon code, click 'Proceed to Checkout', fill in your delivery address, choose a payment method, and place your order. Want me to find something to add to your cart first?"
        )

    if intent in FAQ_ANSWERS:
        return schemas.ChatResponse(reply=FAQ_ANSWERS[intent])

    # product_search: pull keywords out of the message and search the catalog
    stopwords = {"i", "am", "is", "are", "the", "a", "an", "for", "me", "looking",
                 "find", "search", "show", "need", "want", "suggest", "recommend", "please", "some", "any"}
    words = [w for w in re.findall(r"[a-zA-Z]+", payload.message.lower()) if w not in stopwords]
    keyword = " ".join(words) if words else payload.message

    query = db.query(models.Product)
    matches = []
    if keyword.strip():
        like = f"%{keyword}%"
        matches = query.filter(models.Product.name.ilike(like)).limit(6).all()
        if not matches:
            # try matching individual words against name/brand/category
            for w in words:
                like_w = f"%{w}%"
                found = query.filter(models.Product.name.ilike(like_w)).limit(6).all()
                if found:
                    matches = found
                    break

    if matches:
        reply = f"Here's what I found for \"{keyword.strip()}\":"
    else:
        matches = query.order_by(models.Product.rating_avg.desc()).limit(6).all()
        reply = "I couldn't find an exact match, but here are some popular picks you might like:"

    return schemas.ChatResponse(reply=reply, products=matches)
