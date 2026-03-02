from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.order import OrderStatus


# --- Auth ---
class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Category ---
class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    is_visible: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryShort(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    is_visible: bool = True
    model_config = {"from_attributes": True}

class CategoryOut(CategoryBase):
    id: int
    children: list["CategoryOut"] = []
    model_config = {"from_attributes": True}

CategoryOut.model_rebuild()


# --- Product ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    unit: Optional[str] = None
    weight: Optional[str] = None
    photo_url: Optional[str] = None
    category_id: Optional[int] = None
    is_visible: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductShort(BaseModel):
    id: int
    name: str
    price: float
    unit: Optional[str] = None
    weight: Optional[str] = None
    photo_url: Optional[str] = None
    model_config = {"from_attributes": True}

class ProductOut(ProductBase):
    id: int
    category: Optional[CategoryShort] = None
    model_config = {"from_attributes": True}


# --- User ---
class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Order ---
class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product: Optional[ProductShort] = None
    quantity: int
    price_at_order: float
    model_config = {"from_attributes": True}

class OrderOut(BaseModel):
    id: int
    user_id: int
    user: Optional[UserOut] = None
    comment: Optional[str] = None
    status: OrderStatus
    created_at: datetime
    items: list[OrderItemOut] = []
    model_config = {"from_attributes": True}

class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# --- Bot API ---
class BotCreateUser(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None

class BotCartItem(BaseModel):
    product_id: int
    quantity: int

class BotCreateOrder(BaseModel):
    telegram_id: int
    comment: Optional[str] = None
    items: list[BotCartItem]

class OrderItemUpdate(BaseModel):
    quantity: int
