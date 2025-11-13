"""
Database Schemas for SoleStyle

Each Pydantic model represents a collection in MongoDB. Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime

# User and auth -------------------------------------------------------------
class Address(BaseModel):
    full_name: str
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    phone: Optional[str] = None

class User(BaseModel):
    name: str
    email: EmailStr
    password_hash: str
    api_token: Optional[str] = None
    wishlist: List[str] = []
    addresses: List[Address] = []
    is_admin: bool = False

# Product, inventory, reviews ----------------------------------------------
class Variant(BaseModel):
    size: str
    color: str
    texture: Optional[str] = None
    stock: int = 0

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    categories: List[Literal["men","women","kids","sports","formal","casual"]] = []
    images: List[str] = []
    model_url: Optional[str] = None  # .glb / .gltf url
    variants: List[Variant] = []
    rating: float = 0
    ratings_count: int = 0
    featured: bool = False

class Review(BaseModel):
    product_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    created_at: Optional[datetime] = None

# Cart and orders -----------------------------------------------------------
class CartItem(BaseModel):
    product_id: str
    size: str
    color: str
    quantity: int = Field(..., ge=1)
    price: float

class Order(BaseModel):
    user_id: str
    items: List[CartItem]
    amount: float
    status: Literal["created","paid","failed","shipped","delivered","cancelled"] = "created"
    payment_provider: Literal["stripe","razorpay","mock"] = "mock"
    payment_intent_id: Optional[str] = None
    shipping_address: Optional[Address] = None
    created_at: Optional[datetime] = None

# Notifications -------------------------------------------------------------
class NotificationSubscription(BaseModel):
    user_id: Optional[str] = None
    token: str  # fcm/web push token or device token
    platform: Literal["web","ios","android"] = "web"
