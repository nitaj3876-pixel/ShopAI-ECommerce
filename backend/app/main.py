import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine, ensure_schema_upgrades
from app import models  # noqa: F401  (ensures models are registered before create_all)
from app.routers import (
    auth, users, products, cart, wishlist, reviews, orders, recommendations, chatbot, admin
)

load_dotenv()

Base.metadata.create_all(bind=engine)
ensure_schema_upgrades()


def ensure_bootstrap_admin() -> None:
    """Create the configured administrator only when that email is absent.

    This makes an empty local database usable without running the destructive
    demo seeder. Existing users and their roles are never changed here.
    """
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        return
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.email == email.lower()).first():
            from app.auth import hash_password
            db.add(models.User(
                name=os.getenv("ADMIN_NAME", "ShopAI Admin"),
                email=email.lower(),
                hashed_password=hash_password(password),
                is_admin=True,
                is_active=True,
            ))
            db.commit()
    finally:
        db.close()


ensure_bootstrap_admin()

app = FastAPI(
    title="ShopAI — AI-Powered E-Commerce API",
    description="A full-featured e-commerce backend with JWT auth, AI recommendations, and an AI shopping assistant.",
    version="1.0.0",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if frontend_origin == "*" else [frontend_origin, "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(products.categories_router)
app.include_router(cart.router)
app.include_router(wishlist.router)
app.include_router(reviews.router)
app.include_router(orders.router)
app.include_router(recommendations.router)
app.include_router(chatbot.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "message": "ShopAI E-Commerce API is running",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
