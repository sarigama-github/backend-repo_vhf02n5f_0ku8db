import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Review, Order, User, NotificationSubscription

app = FastAPI(title="SoleStyle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities -----------------------------------------------------------------

def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def serialize(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    # Convert ObjectId in nested
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
    return doc


# Basic routes ---------------------------------------------------------------
@app.get("/")
def root():
    return {"name": "SoleStyle", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "❌ Not Configured"
    except Exception as e:
        response["database"] = f"⚠️ Error: {str(e)[:80]}"
    return response

# Products ------------------------------------------------------------------
@app.get("/api/products")
def list_products(category: Optional[str] = None, featured: Optional[bool] = None, q: Optional[str] = None):
    filt = {}
    if category:
        filt["categories"] = category
    if featured is not None:
        filt["featured"] = featured
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}
    items = list(db["product"].find(filt).limit(60)) if db else []
    return [serialize(i) for i in items]

@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    doc = db["product"].find_one({"_id": oid(product_id)})
    if not doc:
        raise HTTPException(404, "Product not found")
    return serialize(doc)

class ProductIn(Product):
    pass

@app.post("/api/admin/products")
def create_product(payload: ProductIn):
    inserted_id = create_document("product", payload)
    return {"id": inserted_id}

@app.put("/api/admin/products/{product_id}")
def update_product(product_id: str, payload: ProductIn):
    if db is None:
        raise HTTPException(500, "Database not configured")
    res = db["product"].update_one({"_id": oid(product_id)}, {"$set": payload.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(404, "Product not found")
    return {"ok": True}

@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: str):
    if db is None:
        raise HTTPException(500, "Database not configured")
    res = db["product"].delete_one({"_id": oid(product_id)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Product not found")
    return {"ok": True}

# Seed sample catalog --------------------------------------------------------
@app.post("/api/admin/seed")
def seed_sample_products():
    if db is None:
        raise HTTPException(500, "Database not configured")

    samples = [
        {
            "title": "SoleStyle Runner X",
            "description": "Lightweight running shoe with breathable mesh and responsive cushioning.",
            "price": 119.99,
            "categories": ["sports", "men"],
            "images": [
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop"
            ],
            "model_url": "https://modelviewer.dev/shared-assets/models/Astronaut.glb",
            "variants": [
                {"size": "8", "color": "black", "stock": 12},
                {"size": "9", "color": "black", "stock": 8},
                {"size": "9", "color": "red", "stock": 5}
            ],
            "featured": True
        },
        {
            "title": "SoleStyle Street Classic",
            "description": "Everyday casual sneaker with clean silhouette and durable rubber sole.",
            "price": 89.0,
            "categories": ["casual", "women"],
            "images": [
                "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200&auto=format&fit=crop"
            ],
            "model_url": "https://modelviewer.dev/shared-assets/models/RobotExpressive.glb",
            "variants": [
                {"size": "6", "color": "white", "stock": 15},
                {"size": "7", "color": "white", "stock": 10},
                {"size": "7", "color": "navy", "stock": 6}
            ],
            "featured": True
        },
        {
            "title": "SoleStyle Court Pro",
            "description": "High-grip court shoe engineered for agility and stability.",
            "price": 129.5,
            "categories": ["sports"],
            "images": [
                "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?q=80&w=1200&auto=format&fit=crop"
            ],
            "model_url": "https://modelviewer.dev/shared-assets/models/Horse.glb",
            "variants": [
                {"size": "8", "color": "black", "stock": 9},
                {"size": "10", "color": "blue", "stock": 4}
            ],
            "featured": False
        },
        # New categories and models
        {
            "title": "SoleStyle Breeze Slip-On",
            "description": "Minimal slip-on for effortless comfort and everyday wear.",
            "price": 79.99,
            "categories": ["casual", "women"],
            "images": [
                "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?q=80&w=1200&auto=format&fit=crop"
            ],
            "model_url": "https://modelviewer.dev/shared-assets/models/Chair.glb",
            "variants": [
                {"size": "6", "color": "white", "stock": 14},
                {"size": "7", "color": "gray", "stock": 10},
                {"size": "8", "color": "black", "stock": 6}
            ],
            "featured": False
        },
        {
            "title": "SoleStyle Executive Oxford",
            "description": "Polished leather oxford for formal occasions and daily elegance.",
            "price": 149.0,
            "categories": ["formal", "men"],
            "images": [
                "https://images.unsplash.com/photo-1511381939415-c1c76e0b9b8e?q=80&w=1200&auto=format&fit=crop"
            ],
            "model_url": "https://modelviewer.dev/shared-assets/models/DamagedHelmet.glb",
            "variants": [
                {"size": "8", "color": "black", "stock": 7},
                {"size": "9", "color": "black", "stock": 9},
                {"size": "10", "color": "brown", "stock": 5},
                {"size": "11", "color": "brown", "stock": 4}
            ],
            "featured": True
        },
        {
            "title": "SoleStyle Mini Runner",
            "description": "Durable and colorful sneakers made for energetic kids.",
            "price": 69.5,
            "categories": ["kids", "casual"],
            "images": [
                "https://images.unsplash.com/photo-1533867617858-e7b1f1fd86d6?q=80&w=1200&auto=format&fit=crop"
            ],
            "model_url": "https://modelviewer.dev/shared-assets/models/Buggy.glb",
            "variants": [
                {"size": "2", "color": "blue", "stock": 12},
                {"size": "3", "color": "pink", "stock": 10},
                {"size": "4", "color": "green", "stock": 8}
            ],
            "featured": False
        },
        {
            "title": "SoleStyle Street High-Top",
            "description": "Iconic high-top silhouette with padded collar and bold style.",
            "price": 99.0,
            "categories": ["casual", "men"],
            "images": [
                "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200&auto=format&fit=crop"
            ],
            "model_url": "https://modelviewer.dev/shared-assets/models/Chair.glb",
            "variants": [
                {"size": "9", "color": "black", "stock": 10},
                {"size": "10", "color": "white", "stock": 7},
                {"size": "11", "color": "black", "stock": 5}
            ],
            "featured": False
        },
        {
            "title": "SoleStyle Swift Trainer",
            "description": "Responsive trainer designed for sprints and gym sessions.",
            "price": 109.0,
            "categories": ["sports", "women"],
            "images": [
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop"
            ],
            "model_url": "https://modelviewer.dev/shared-assets/models/Astronaut.glb",
            "variants": [
                {"size": "6", "color": "teal", "stock": 9},
                {"size": "7", "color": "teal", "stock": 7},
                {"size": "8", "color": "black", "stock": 6}
            ],
            "featured": True
        }
    ]

    created = []
    for s in samples:
        exists = db["product"].find_one({"title": s["title"]})
        if exists:
            continue
        res = db["product"].insert_one(s)
        created.append(str(res.inserted_id))

    return {"created": created, "total": db["product"].count_documents({})}

# Reviews -------------------------------------------------------------------
class ReviewIn(Review):
    pass

@app.get("/api/products/{product_id}/reviews")
def get_reviews(product_id: str):
    items = list(db["review"].find({"product_id": product_id}).sort("created_at", -1)) if db else []
    return [serialize(i) for i in items]

@app.post("/api/products/{product_id}/reviews")
def add_review(product_id: str, payload: ReviewIn):
    if payload.product_id != product_id:
        payload.product_id = product_id
    inserted_id = create_document("review", payload)
    return {"id": inserted_id}

# Orders and checkout (mock payment intent for demo) ------------------------
class CreateOrderPayload(BaseModel):
    user_id: Optional[str] = None
    items: List[dict]
    amount: float
    provider: Optional[str] = "mock"  # stripe | razorpay | mock

@app.post("/api/checkout/create-intent")
def create_payment_intent(payload: CreateOrderPayload):
    # For demo we return a mock client secret
    client_secret = f"mock_secret_{ObjectId()}"
    order = Order(
        user_id=payload.user_id or "guest",
        items=[
            # trust client for demo; real impl should fetch product prices
            __import__("pydantic").BaseModel.construct(**{
                "product_id": i.get("product_id"),
                "size": i.get("size"),
                "color": i.get("color"),
                "quantity": i.get("quantity", 1),
                "price": i.get("price", 0.0),
            }) for i in payload.items
        ],
        amount=payload.amount,
        payment_provider=payload.provider or "mock",
        payment_intent_id=client_secret,
    )
    order_id = create_document("order", order)
    return {"client_secret": client_secret, "order_id": order_id}

# Wishlist ------------------------------------------------------------------
@app.post("/api/users/{user_id}/wishlist")
def toggle_wishlist(user_id: str, product_id: str):
    if db is None:
        raise HTTPException(500, "Database not configured")
    user = db["user"].find_one({"_id": oid(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    exists = product_id in (user.get("wishlist") or [])
    op = {"$pull": {"wishlist": product_id}} if exists else {"$addToSet": {"wishlist": product_id}}
    db["user"].update_one({"_id": oid(user_id)}, op)
    return {"in_wishlist": not exists}

# Auth (very simple demo) ---------------------------------------------------
class RegisterPayload(BaseModel):
    name: str
    email: str
    password: str

@app.post("/api/auth/register")
def register(payload: RegisterPayload):
    if db is None:
        raise HTTPException(500, "Database not configured")
    exists = db["user"].find_one({"email": payload.email})
    if exists:
        raise HTTPException(400, "Email already registered")
    # naive password hashing for demo only
    import hashlib
    password_hash = hashlib.sha256(payload.password.encode()).hexdigest()
    user = User(name=payload.name, email=payload.email, password_hash=password_hash)
    user_id = create_document("user", user)
    return {"id": user_id}

class LoginPayload(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
def login(payload: LoginPayload):
    if db is None:
        raise HTTPException(500, "Database not configured")
    import hashlib, secrets
    password_hash = hashlib.sha256(payload.password.encode()).hexdigest()
    user = db["user"].find_one({"email": payload.email, "password_hash": password_hash})
    if not user:
        raise HTTPException(401, "Invalid credentials")
    token = secrets.token_hex(16)
    db["user"].update_one({"_id": user["_id"]}, {"$set": {"api_token": token}})
    return {"token": token, "user": serialize(user)}

# Notification subscription (mock) ------------------------------------------
@app.post("/api/subscribe")
def subscribe_notifs(payload: NotificationSubscription):
    sub_id = create_document("notificationsubscription", payload)
    return {"id": sub_id}

# SEO schema exposure (simple) ----------------------------------------------
@app.get("/sitemap")
def sitemap():
    products = list(db["product"].find({}, {"_id": 1})) if db else []
    urls = [f"/product/{str(p['_id'])}" for p in products]
    return {"urls": urls}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
