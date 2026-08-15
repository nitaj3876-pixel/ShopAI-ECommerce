"""Pydantic schemas used for request validation and API responses."""
import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- Auth / User ----------

class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=100)


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    is_admin: bool
    created_at: datetime.datetime


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Address ----------

class AddressCreate(BaseModel):
    full_name: str
    phone: str
    line1: str
    city: str
    state: str
    pincode: str
    is_default: bool = False


class AddressOut(AddressCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Category ----------

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    image_url: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str
    image_url: Optional[str] = None


# ---------- Product ----------

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    specifications: Optional[str] = None
    brand: Optional[str] = None
    price: float = Field(ge=0)
    mrp: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    image_urls: str = Field(min_length=1)  # comma-separated
    category_id: int = Field(gt=0)
    is_featured: bool = False
    is_best_seller: bool = False
    is_trending: bool = False
    is_flash_sale: bool = False
    seller_name: Optional[str] = "ShopAI Retail"


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1)
    specifications: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    mrp: Optional[float] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)
    image_urls: Optional[str] = None
    category_id: Optional[int] = Field(default=None, gt=0)
    is_featured: Optional[bool] = None
    is_best_seller: Optional[bool] = None
    is_trending: Optional[bool] = None
    is_flash_sale: Optional[bool] = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str
    specifications: Optional[str] = None
    brand: Optional[str] = None
    price: float
    mrp: float
    stock: int
    image_urls: str
    rating_avg: float
    rating_count: int
    is_featured: bool
    is_best_seller: bool
    is_trending: bool
    is_flash_sale: bool
    seller_name: str
    category_id: int
    is_active: bool = True
    discount_percent: int = 0


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    price: float
    mrp: float
    stock: int
    image_urls: str
    rating_avg: float
    rating_count: int
    discount_percent: int = 0
    category_id: int


# ---------- Cart ----------

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity: int
    product: ProductListItem


class CartSummary(BaseModel):
    items: List[CartItemOut]
    subtotal: float
    discount: float
    delivery_charge: float
    gst_amount: float
    grand_total: float


# ---------- Wishlist ----------

class WishlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    product: ProductListItem


# ---------- Reviews ----------

class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    product_id: int
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime.datetime


# ---------- Orders / Checkout ----------

class CheckoutRequest(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    address_line: str
    city: str
    state: str
    pincode: str
    payment_method: str  # cod | razorpay | stripe | upi
    coupon_code: Optional[str] = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    product_image_urls: Optional[str] = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    status: str
    subtotal: float
    discount: float
    delivery_charge: float
    gst_amount: float
    grand_total: float
    shipping_name: str
    shipping_address: str
    shipping_city: str
    shipping_state: str
    shipping_pincode: str
    created_at: datetime.datetime
    items: List[OrderItemOut]


class OrderStatusUpdate(BaseModel):
    status: str


# ---------- Coupon ----------

class CouponCreate(BaseModel):
    code: str
    description: Optional[str] = None
    discount_percent: float
    min_order_value: float = 0
    expires_at: Optional[datetime.datetime] = None


class CouponOut(CouponCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


# ---------- Chatbot ----------

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    products: List[ProductListItem] = []


# ---------- Admin analytics ----------

class DashboardStats(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_revenue: float
    pending_orders: int
    total_categories: int
    total_stock: int
    low_stock_products: int
    out_of_stock_products: int
