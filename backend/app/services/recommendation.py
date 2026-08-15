"""
Content-based AI recommendation engine.

Builds a TF-IDF matrix over each product's name + brand + category + description,
then uses cosine similarity to find related items. This powers:
  - "Similar Products" on the product detail page
  - "Frequently Bought Together" (co-occurrence in past orders, blended with content similarity)
  - "Personalized Recommendations" (based on a user's order + recently-viewed history)

Rebuilt on-demand each call for simplicity. For a large catalog this would be
cached/recomputed on a schedule instead of per-request.
"""
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app import models


def _build_corpus(db):
    products = db.query(models.Product).filter(models.Product.is_active.is_(True)).all()
    if not products:
        return [], None, None

    documents = []
    for p in products:
        category_name = p.category.name if p.category else ""
        text = " ".join(filter(None, [p.name, p.brand or "", category_name, p.description]))
        documents.append(text)

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(documents)
    return products, matrix, vectorizer


def get_similar_products(db, product_id: int, top_n: int = 8) -> list[int]:
    products, matrix, _ = _build_corpus(db)
    if not products:
        return []

    ids = [p.id for p in products]
    if product_id not in ids:
        return []

    idx = ids.index(product_id)
    similarities = cosine_similarity(matrix[idx], matrix).flatten()

    ranked = sorted(
        ((score, pid) for score, pid in zip(similarities, ids) if pid != product_id),
        key=lambda x: x[0],
        reverse=True,
    )
    return [pid for _, pid in ranked[:top_n]]


def get_frequently_bought_together(db, product_id: int, top_n: int = 4) -> list[int]:
    """Finds products that co-occur most often with product_id across all past orders."""
    order_ids_with_product = [
        oi.order_id for oi in db.query(models.OrderItem).filter(models.OrderItem.product_id == product_id).all()
    ]
    if not order_ids_with_product:
        return get_similar_products(db, product_id, top_n)

    co_occurring = db.query(models.OrderItem.product_id).filter(
        models.OrderItem.order_id.in_(order_ids_with_product),
        models.OrderItem.product_id != product_id,
    ).all()
    counts = Counter(pid for (pid,) in co_occurring)
    if not counts:
        return get_similar_products(db, product_id, top_n)

    return [pid for pid, _ in counts.most_common(top_n)]


def get_personalized_recommendations(db, user_id: int, top_n: int = 12) -> list[int]:
    """Blends a user's order history + recently-viewed items into a taste profile,
    then ranks the catalog by similarity to that profile."""
    products, matrix, vectorizer = _build_corpus(db)
    if not products:
        return []
    ids = [p.id for p in products]

    ordered_ids = {
        oi.product_id for oi in db.query(models.OrderItem).join(models.Order).filter(
            models.Order.user_id == user_id
        ).all()
    }
    viewed_ids = {
        rv.product_id for rv in db.query(models.RecentlyViewed).filter(
            models.RecentlyViewed.user_id == user_id
        ).all()
    }
    wishlist_ids = {
        w.product_id for w in db.query(models.WishlistItem).filter(
            models.WishlistItem.user_id == user_id
        ).all()
    }

    seed_ids = ordered_ids | viewed_ids | wishlist_ids
    if not seed_ids:
        # No history yet — fall back to best sellers / top rated.
        top = db.query(models.Product).filter(models.Product.is_active.is_(True)).order_by(
            models.Product.rating_avg.desc(), models.Product.rating_count.desc()
        ).limit(top_n).all()
        return [p.id for p in top]

    seed_indices = [ids.index(pid) for pid in seed_ids if pid in ids]
    if not seed_indices:
        return []

    profile_vector = matrix[seed_indices].mean(axis=0)
    import numpy as np
    profile_vector = np.asarray(profile_vector)

    similarities = cosine_similarity(profile_vector, matrix).flatten()
    ranked = sorted(
        ((score, pid) for score, pid in zip(similarities, ids) if pid not in seed_ids),
        key=lambda x: x[0],
        reverse=True,
    )
    return [pid for _, pid in ranked[:top_n]]
