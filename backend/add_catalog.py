"""Add a non-destructive starter catalog to the existing ShopAI SQLite database.

The script never deletes or resets rows. It inserts only the categories and
products below whose slugs are not already present, so it can be re-run safely.
"""
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("ecommerce.db")

CATEGORIES = [
    ("Electronics", "electronics"),
    ("Fashion", "fashion"),
    ("Home & Kitchen", "home-kitchen"),
    ("Beauty & Personal Care", "beauty-personal-care"),
    ("Sports & Fitness", "sports-fitness"),
]

PRODUCTS = [
    ("Nova X5 Smartphone", "electronics", "NovaTech", 18999, 21999, 24),
    ("Pulse Wireless Earbuds", "electronics", "PulseWear", 1799, 2499, 40),
    ("VoltEdge 20000mAh Power Bank", "electronics", "VoltEdge", 1499, 1999, 35),
    ("SonicWave Bluetooth Speaker", "electronics", "SonicWave", 2299, 2999, 18),
    ("NovaTech 15-inch Laptop", "electronics", "NovaTech", 54999, 61999, 9),
    ("Pulse Smartwatch Active", "electronics", "PulseWear", 2999, 3999, 28),
    ("VoltEdge Fast Charger 33W", "electronics", "VoltEdge", 699, 999, 60),
    ("SonicWave Over-Ear Headphones", "electronics", "SonicWave", 3299, 4299, 17),
    ("Nova HD Webcam", "electronics", "NovaTech", 1299, 1699, 22),
    ("VoltEdge LED Desk Lamp", "electronics", "VoltEdge", 899, 1299, 31),
    ("Urbanova Cotton T-Shirt", "fashion", "Urbanova", 499, 799, 50),
    ("TrendSetter Slim Fit Jeans", "fashion", "TrendSetter", 1199, 1699, 32),
    ("Urbanova Casual Sneakers", "fashion", "Urbanova", 1499, 2199, 20),
    ("TrendSetter Office Shirt", "fashion", "TrendSetter", 899, 1299, 27),
    ("Urbanova Everyday Backpack", "fashion", "Urbanova", 1099, 1599, 16),
    ("TrendSetter Classic Watch", "fashion", "TrendSetter", 1799, 2499, 12),
    ("Urbanova Summer Dress", "fashion", "Urbanova", 1299, 1899, 25),
    ("TrendSetter Leather Wallet", "fashion", "TrendSetter", 599, 899, 44),
    ("Urbanova Hooded Jacket", "fashion", "Urbanova", 1999, 2899, 11),
    ("TrendSetter Canvas Belt", "fashion", "TrendSetter", 349, 499, 55),
    ("CraftHome Non-stick Cookware Set", "home-kitchen", "CraftHome", 2499, 3499, 15),
    ("EcoNest Bamboo Storage Basket", "home-kitchen", "EcoNest", 699, 999, 36),
    ("CraftHome Mixer Grinder", "home-kitchen", "CraftHome", 3299, 4499, 13),
    ("EcoNest Steel Water Bottle", "home-kitchen", "EcoNest", 449, 699, 48),
    ("CraftHome Microfiber Bedsheet", "home-kitchen", "CraftHome", 899, 1399, 30),
    ("EcoNest Glass Food Container Set", "home-kitchen", "EcoNest", 1199, 1699, 21),
    ("CraftHome Air Fryer 4L", "home-kitchen", "CraftHome", 4999, 6499, 8),
    ("EcoNest Indoor Planter Set", "home-kitchen", "EcoNest", 799, 1199, 34),
    ("CraftHome Memory Foam Pillow", "home-kitchen", "CraftHome", 999, 1499, 19),
    ("EcoNest Laundry Bag", "home-kitchen", "EcoNest", 399, 599, 42),
    ("GlowUp Vitamin C Face Serum", "beauty-personal-care", "GlowUp", 649, 899, 38),
    ("PureLife Gentle Face Wash", "beauty-personal-care", "PureLife", 299, 399, 64),
    ("GlowUp Matte Lipstick Set", "beauty-personal-care", "GlowUp", 799, 1099, 29),
    ("PureLife SPF 50 Sunscreen", "beauty-personal-care", "PureLife", 449, 649, 41),
    ("GlowUp Hair Dryer", "beauty-personal-care", "GlowUp", 1599, 2199, 14),
    ("PureLife Body Lotion", "beauty-personal-care", "PureLife", 349, 499, 52),
    ("GlowUp Perfume Mist", "beauty-personal-care", "GlowUp", 999, 1499, 23),
    ("PureLife Herbal Shampoo", "beauty-personal-care", "PureLife", 379, 549, 46),
    ("GlowUp Makeup Brush Kit", "beauty-personal-care", "GlowUp", 899, 1299, 20),
    ("PureLife Electric Toothbrush", "beauty-personal-care", "PureLife", 1299, 1799, 10),
    ("MaxFit Premium Yoga Mat", "sports-fitness", "MaxFit", 799, 1199, 37),
    ("PrimeGear Adjustable Dumbbells", "sports-fitness", "PrimeGear", 2999, 3999, 12),
    ("MaxFit Resistance Band Set", "sports-fitness", "MaxFit", 499, 699, 53),
    ("PrimeGear Football", "sports-fitness", "PrimeGear", 899, 1299, 26),
    ("MaxFit Steel Water Bottle", "sports-fitness", "MaxFit", 549, 799, 45),
    ("PrimeGear Cricket Bat", "sports-fitness", "PrimeGear", 1899, 2699, 11),
    ("MaxFit Gym Gloves", "sports-fitness", "MaxFit", 399, 599, 39),
    ("PrimeGear Skipping Rope", "sports-fitness", "PrimeGear", 299, 449, 61),
    ("MaxFit Foam Roller", "sports-fitness", "MaxFit", 699, 999, 24),
    ("PrimeGear Sports Duffel Bag", "sports-fitness", "PrimeGear", 1399, 1999, 18),
]


def slugify(name: str) -> str:
    return "-".join(name.lower().replace("&", "and").split())


def run() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.cursor()
        category_ids = {}
        for name, slug in CATEGORIES:
            cursor.execute("SELECT id FROM categories WHERE slug = ?", (slug,))
            row = cursor.fetchone()
            if row:
                category_ids[slug] = row[0]
                continue
            cursor.execute(
                "INSERT INTO categories (name, slug, image_url) VALUES (?, ?, ?)",
                (name, slug, f"https://picsum.photos/seed/category-{slug}/300/300"),
            )
            category_ids[slug] = cursor.lastrowid

        product_columns = {row[1] for row in cursor.execute("PRAGMA table_info(products)")}
        has_is_active = "is_active" in product_columns
        added = 0
        for index, (name, category_slug, brand, price, mrp, stock) in enumerate(PRODUCTS, start=1):
            slug = slugify(name)
            cursor.execute("SELECT id FROM products WHERE slug = ?", (slug,))
            if cursor.fetchone():
                continue
            fields = [
                "name", "slug", "description", "specifications", "brand", "price", "mrp", "stock",
                "image_urls", "rating_avg", "rating_count", "is_featured", "is_best_seller",
                "is_trending", "is_flash_sale", "seller_name", "category_id",
            ]
            values = [
                name, slug, f"Quality {name} for everyday use.", f"Brand: {brand}", brand, price, mrp, stock,
                f"https://picsum.photos/seed/{slug}/600/600", 0, 0, int(index % 5 == 0),
                int(index % 4 == 0), int(index % 3 == 0), int(index % 10 == 0),
                f"{brand} Official Store", category_ids[category_slug],
            ]
            if has_is_active:
                fields.append("is_active")
                values.append(1)
            placeholders = ", ".join("?" for _ in fields)
            cursor.execute(
                f"INSERT INTO products ({', '.join(fields)}) VALUES ({placeholders})", values
            )
            added += 1
        connection.commit()
        print(f"Added {added} product(s). Catalog now contains {cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]} products.")
    finally:
        connection.close()


if __name__ == "__main__":
    run()
