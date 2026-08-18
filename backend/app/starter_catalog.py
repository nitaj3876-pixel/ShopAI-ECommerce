"""Create a small, non-destructive storefront catalog for a new database."""

from app import models
from app.database import SessionLocal


STARTER_CATEGORIES = [
    ("Electronics", "electronics"),
    ("Fashion", "fashion"),
    ("Home & Kitchen", "home-kitchen"),
    ("Beauty & Personal Care", "beauty-personal-care"),
    ("Sports & Fitness", "sports-fitness"),
]

# name, category slug, brand, price, mrp, stock, featured, bestseller, trending, flash sale
STARTER_PRODUCTS = [
    ("Nova X5 Smartphone", "electronics", "NovaTech", 18999, 21999, 24, True, True, True, True),
    ("Pulse Wireless Earbuds", "electronics", "PulseWear", 1799, 2499, 40, True, True, True, True),
    ("VoltEdge Power Bank 20000mAh", "electronics", "VoltEdge", 1499, 1999, 35, False, True, False, True),
    ("Urbanova Casual Sneakers", "fashion", "Urbanova", 1499, 2199, 20, True, True, True, False),
    ("TrendSetter Slim Fit Jeans", "fashion", "TrendSetter", 1199, 1699, 32, False, True, False, True),
    ("CraftHome Air Fryer 4L", "home-kitchen", "CraftHome", 4999, 6499, 8, True, False, True, False),
    ("EcoNest Steel Water Bottle", "home-kitchen", "EcoNest", 449, 699, 48, False, True, True, True),
    ("GlowUp Vitamin C Face Serum", "beauty-personal-care", "GlowUp", 649, 899, 38, True, True, True, False),
    ("PureLife SPF 50 Sunscreen", "beauty-personal-care", "PureLife", 449, 649, 41, False, False, True, True),
    ("MaxFit Premium Yoga Mat", "sports-fitness", "MaxFit", 799, 1199, 37, True, True, False, False),
    ("PrimeGear Adjustable Dumbbells", "sports-fitness", "PrimeGear", 2999, 3999, 12, False, True, True, False),
    ("SonicWave Bluetooth Speaker", "electronics", "SonicWave", 2299, 2999, 18, True, False, True, True),
]


def _slugify(name: str) -> str:
    return "-".join(name.lower().replace("&", "and").split())


def ensure_starter_catalog() -> None:
    """Populate only a completely empty catalog; never overwrite store data."""
    db = SessionLocal()
    try:
        if db.query(models.Product).filter(models.Product.is_active.is_(True)).first():
            return

        categories = {}
        for name, slug in STARTER_CATEGORIES:
            category = db.query(models.Category).filter(models.Category.slug == slug).first()
            if not category:
                category = models.Category(
                    name=name,
                    slug=slug,
                    image_url=f"https://picsum.photos/seed/category-{slug}/300/300",
                )
                db.add(category)
                db.flush()
            categories[slug] = category

        for index, item in enumerate(STARTER_PRODUCTS, start=1):
            name, category_slug, brand, price, mrp, stock, featured, bestseller, trending, flash_sale = item
            slug = _slugify(name)
            if db.query(models.Product).filter(models.Product.slug == slug).first():
                continue
            db.add(models.Product(
                name=name,
                slug=slug,
                description=f"Quality {name} for everyday use.",
                specifications=f"Brand: {brand}",
                brand=brand,
                price=price,
                mrp=mrp,
                stock=stock,
                image_urls=f"https://picsum.photos/seed/{slug}/600/600",
                rating_avg=round(4.0 + (index % 10) / 10, 1),
                rating_count=12 + index,
                is_featured=featured,
                is_best_seller=bestseller,
                is_trending=trending,
                is_flash_sale=flash_sale,
                seller_name=f"{brand} Official Store",
                category_id=categories[category_slug].id,
                is_active=True,
            ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
