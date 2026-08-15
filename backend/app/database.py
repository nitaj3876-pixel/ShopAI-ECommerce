"""
Database connection setup.

Defaults to SQLite so the project runs instantly with zero setup.
Set DATABASE_URL in .env to a PostgreSQL URL for production use, e.g.:
    postgresql://ecommerce_user:ecommerce_pass@localhost:5432/ecommerce_db
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_upgrades():
    """Apply the one additive catalog migration needed by the admin panel.

    This intentionally performs no reset or data rewrite. Existing SQLite files
    receive an ``is_active`` column once; new databases receive it via metadata.
    """
    inspector = inspect(engine)
    if "products" not in inspector.get_table_names():
        return
    product_columns = {column["name"] for column in inspector.get_columns("products")}
    if "is_active" not in product_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE products ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
