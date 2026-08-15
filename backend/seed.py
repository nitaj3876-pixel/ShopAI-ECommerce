"""
Generates demo data for the ShopAI store:
  15 categories, 100 products, 200 users, ~500 orders, reviews, ratings, coupons.

Run with:  python seed.py
Re-running wipes and recreates all tables first.
"""
import os
import random
import datetime
import sys

sys.path.insert(0, os.path.dirname(__file__))

from faker import Faker
from app.database import Base, engine, SessionLocal
from app import models
from app.auth import hash_password

fake = Faker()
random.seed(42)
Faker.seed(42)

print("Resetting database...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

CATEGORY_DATA = {
    "Electronics": ["Smartphone", "Laptop", "Bluetooth Earbuds", "Smartwatch", "Power Bank", "Tablet", "Camera", "Gaming Console"],
    "Mobiles": ["5G Smartphone", "Budget Phone", "Flagship Phone", "Phone Cover", "Screen Protector"],
    "Fashion - Men": ["Men's T-Shirt", "Men's Jeans", "Men's Formal Shirt", "Men's Jacket", "Men's Sneakers"],
    "Fashion - Women": ["Women's Kurti", "Women's Dress", "Women's Handbag", "Women's Sandals", "Women's Saree"],
    "Home & Kitchen": ["Mixer Grinder", "Non-Stick Cookware Set", "Air Fryer", "Water Bottle Set", "LED Table Lamp"],
    "Furniture": ["Study Table", "Office Chair", "Bookshelf", "Bean Bag", "Wardrobe"],
    "Beauty & Personal Care": ["Face Wash", "Sunscreen", "Hair Dryer", "Perfume", "Lipstick Set"],
    "Books": ["Self-Help Book", "Fiction Novel", "Programming Guide", "Cookbook", "Children's Storybook"],
    "Sports & Fitness": ["Yoga Mat", "Dumbbell Set", "Cricket Bat", "Football", "Resistance Bands"],
    "Toys & Baby": ["Building Blocks Set", "Remote Control Car", "Baby Stroller", "Soft Toy", "Puzzle Game"],
    "Grocery": ["Organic Rice 5kg", "Cold Pressed Oil 1L", "Green Tea Pack", "Protein Bar Box", "Dry Fruits Combo"],
    "Appliances": ["Refrigerator", "Washing Machine", "Microwave Oven", "Air Conditioner", "Water Purifier"],
    "Automotive": ["Car Phone Holder", "Car Vacuum Cleaner", "Bike Helmet", "Car Seat Cover", "Tyre Inflator"],
    "Musical Instruments": ["Acoustic Guitar", "Digital Keyboard", "Drum Pad", "Violin", "Ukulele"],
    "Pet Supplies": ["Dog Food 3kg", "Cat Litter Box", "Pet Grooming Kit", "Dog Leash", "Pet Bed"],
}

BRANDS = ["Zynetic", "Urbanova", "NovaTech", "PulseWear", "CraftHome", "VoltEdge", "PureLife",
          "TrendSetter", "AquaFresh", "PrimeGear", "EcoNest", "SonicWave", "MaxFit", "GlowUp", "DailyBasics"]

IMG_PLACEHOLDER = "https://picsum.photos/seed/{seed}/600/600"


def make_products():
    products = []
    pid_counter = 1
    categories = db.query(models.Category).all()

    total_needed = 100
    all_names = []
    for cat in categories:
        for base_name in CATEGORY_DATA[cat.name]:
            all_names.append((cat, base_name))

    random.shuffle(all_names)
    # Cycle through the pool of category/base-name pairs until we hit 100 products.
    i = 0
    while len(products) < total_needed:
        cat, base_name = all_names[i % len(all_names)]
        i += 1
        brand = random.choice(BRANDS)
        variant = random.choice(["Pro", "Max", "Lite", "Plus", "Classic", "2.0", "Air", ""])
        name = f"{brand} {base_name} {variant}".strip()

        mrp = round(random.uniform(299, 79999), 2)
        discount = random.choice([0, 5, 10, 15, 20, 25, 30, 40])
        price = round(mrp * (1 - discount / 100), 2)
        stock = random.randint(0, 250)

        slug_base = "-".join(name.lower().split())
        slug = slug_base
        n = 1
        existing_slugs = {p["slug"] for p in products}
        while slug in existing_slugs:
            n += 1
            slug = f"{slug_base}-{n}"

        seed_img = f"{cat.slug}-{pid_counter}"
        product = {
            "name": name,
            "slug": slug,
            "description": fake.paragraph(nb_sentences=5),
            "specifications": f"Brand: {brand} | Model: {base_name} | Warranty: {random.choice([1,2,3])} Year(s)",
            "brand": brand,
            "price": price,
            "mrp": mrp,
            "stock": stock,
            "image_urls": ",".join(IMG_PLACEHOLDER.format(seed=f"{seed_img}-{k}") for k in range(3)),
            "category_id": cat.id,
            "is_featured": random.random() < 0.15,
            "is_best_seller": random.random() < 0.15,
            "is_trending": random.random() < 0.15,
            "is_flash_sale": random.random() < 0.10,
            "seller_name": f"{brand} Official Store",
        }
        products.append(product)
        pid_counter += 1

    return products


def run():
    print("Creating categories...")
    categories = []
    for name in CATEGORY_DATA:
        slug = "-".join(name.lower().replace("&", "and").split())
        cat = models.Category(name=name, slug=slug, image_url=IMG_PLACEHOLDER.format(seed=slug))
        db.add(cat)
        categories.append(cat)
    db.commit()

    print("Creating products...")
    product_dicts = make_products()
    products = [models.Product(**pd) for pd in product_dicts]
    db.add_all(products)
    db.commit()
    for p in products:
        db.refresh(p)

    print("Creating admin account...")
    admin = models.User(
        name="ShopAI Admin",
        email=os.getenv("ADMIN_EMAIL", "admin@shopai.com"),
        phone=fake.phone_number()[:20],
        hashed_password=hash_password(os.getenv("ADMIN_PASSWORD", "Admin@123")),
        is_admin=True,
    )
    db.add(admin)
    db.commit()

    print("Creating 200 users...")
    users = []
    for _ in range(200):
        email = fake.unique.email()
        user = models.User(
            name=fake.name(),
            email=email,
            phone=fake.phone_number()[:20],
            hashed_password=hash_password("Password@123"),
        )
        users.append(user)
    db.add_all(users)
    db.commit()
    for u in users:
        db.refresh(u)

    print("Creating addresses...")
    for user in random.sample(users, 150):
        db.add(models.Address(
            user_id=user.id,
            full_name=user.name,
            phone=user.phone,
            line1=fake.street_address(),
            city=fake.city(),
            state=fake.state(),
            pincode=fake.postcode(),
            is_default=True,
        ))
    db.commit()

    print("Creating coupons...")
    coupons = [
        models.Coupon(code="WELCOME10", description="10% off on your first order", discount_percent=10, min_order_value=499),
        models.Coupon(code="FLAT20", description="Flat 20% off", discount_percent=20, min_order_value=1499),
        models.Coupon(code="MEGA30", description="Mega sale — 30% off", discount_percent=30, min_order_value=2999),
        models.Coupon(code="FREESHIP", description="Small discount to offset delivery", discount_percent=5, min_order_value=299),
    ]
    db.add_all(coupons)
    db.commit()

    print("Creating ~500 orders...")
    statuses = list(models.OrderStatus)
    payment_methods = list(models.PaymentMethod)
    order_count = 0
    for _ in range(500):
        user = random.choice(users)
        basket = random.sample(products, k=random.randint(1, 4))
        subtotal = sum(p.price * random.randint(1, 3) for p in basket)
        if subtotal <= 0:
            continue
        discount = round(subtotal * random.choice([0, 0, 0.1, 0.2]), 2)
        gst = round((subtotal - discount) * 0.18, 2)
        delivery = 0 if subtotal >= 999 else 49
        grand_total = round(subtotal - discount + gst + delivery, 2)

        created_at = fake.date_time_between(start_date="-6M", end_date="now")
        order = models.Order(
            order_number="ORD" + str(random.randint(10000000, 99999999)),
            user_id=user.id,
            subtotal=round(subtotal, 2),
            discount=discount,
            delivery_charge=delivery,
            gst_amount=gst,
            grand_total=grand_total,
            status=random.choice(statuses),
            shipping_name=user.name,
            shipping_phone=user.phone or fake.phone_number()[:20],
            shipping_address=fake.street_address(),
            shipping_city=fake.city(),
            shipping_state=fake.state(),
            shipping_pincode=fake.postcode(),
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(order)
        db.flush()

        for p in basket:
            qty = random.randint(1, 3)
            db.add(models.OrderItem(
                order_id=order.id,
                product_id=p.id,
                product_name=p.name,
                unit_price=p.price,
                quantity=qty,
            ))

        db.add(models.Payment(
            order_id=order.id,
            method=random.choice(payment_methods),
            status=random.choice(list(models.PaymentStatus)),
            transaction_ref=f"TXN{random.randint(100000,999999)}",
            amount=grand_total,
        ))
        order_count += 1
    db.commit()
    print(f"Created {order_count} orders.")

    print("Creating reviews & ratings...")
    review_count = 0
    for product in products:
        for user in random.sample(users, k=random.randint(0, 8)):
            existing = db.query(models.Review).filter(
                models.Review.user_id == user.id, models.Review.product_id == product.id
            ).first()
            if existing:
                continue
            rating = random.choices([5, 4, 3, 2, 1], weights=[40, 30, 15, 10, 5])[0]
            db.add(models.Review(
                user_id=user.id,
                product_id=product.id,
                rating=rating,
                title=random.choice(["Great product!", "Value for money", "As described", "Could be better", "Loved it"]),
                comment=fake.sentence(nb_words=15),
            ))
            review_count += 1
    db.commit()

    print("Recalculating product ratings...")
    for product in products:
        reviews = db.query(models.Review).filter(models.Review.product_id == product.id).all()
        if reviews:
            product.rating_avg = round(sum(r.rating for r in reviews) / len(reviews), 1)
            product.rating_count = len(reviews)
    db.commit()

    print("Creating wishlist & cart samples...")
    for user in random.sample(users, 80):
        for p in random.sample(products, k=random.randint(1, 5)):
            exists = db.query(models.WishlistItem).filter(
                models.WishlistItem.user_id == user.id, models.WishlistItem.product_id == p.id
            ).first()
            if not exists:
                db.add(models.WishlistItem(user_id=user.id, product_id=p.id))
    db.commit()

    print("\nDone!")
    print(f"  Categories: {len(categories)}")
    print(f"  Products:   {len(products)}")
    print(f"  Users:      {len(users)} + 1 admin")
    print(f"  Orders:     {order_count}")
    print(f"  Reviews:    {review_count}")
    print(f"\n  Admin login -> email: {admin.email}  password: {os.getenv('ADMIN_PASSWORD', 'Admin@123')}")
    print(f"  Sample user login -> email: {users[0].email}  password: Password@123")


if __name__ == "__main__":
    run()
    db.close()
