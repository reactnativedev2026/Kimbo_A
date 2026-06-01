from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    CONTRACTOR = "contractor"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: UserRole = Field(default=UserRole.CONTRACTOR)
    
    # Contractor / User Details
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    full_name: str
    password: str
    
    contractor_code: Optional[str] = Field(default=None, unique=True)
    mobile_number: Optional[str] = Field(default=None)
    address: Optional[str] = None
    gst_details: Optional[str] = None
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    
    profile_image: Optional[str] = Field(default=None)
    govt_id: Optional[str] = Field(default=None)
    
    total_tokens: int = Field(default=0)

    # Relationships
    material_transfers: List["MaterialTransfer"] = Relationship(back_populates="contractor")
    purchase_entries: List["PurchaseEntry"] = Relationship(back_populates="contractor")
    reward_requests: List["RewardRedeem"] = Relationship(back_populates="contractor")


class MaterialTransfer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transfer_id: str = Field(unique=True)
    date: datetime = Field(default_factory=datetime.utcnow)
    contractor_id: int = Field(foreign_key="user.id")
    material_type: str
    quantity: float
    unit: str
    vehicle_number: Optional[str] = None
    driver_details: Optional[str] = None
    notes: Optional[str] = None

    contractor: User = Relationship(back_populates="material_transfers")


class PurchaseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class PurchaseEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(default_factory=datetime.utcnow)
    contractor_id: int = Field(foreign_key="user.id")
    
    # Link to the newly created Product model instead of generic string
    product_id: int = Field(foreign_key="product.id")
    quantity_bought: float # quantity
    total_amount: float
    bill_number: Optional[str] = None
    
    status: PurchaseStatus = Field(default=PurchaseStatus.PENDING)
    tokens_earned: int = Field(default=0)

    contractor: User = Relationship(back_populates="purchase_entries")
    product: "Product" = Relationship()


class Scheme(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    start_date: datetime
    end_date: datetime
    banner_image: Optional[str] = None
    is_active: bool = Field(default=True)


class RedeemStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class RewardRedeem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(default_factory=datetime.utcnow)
    contractor_id: int = Field(foreign_key="user.id")
    tokens_used: int
    reward_description: str
    status: RedeemStatus = Field(default=RedeemStatus.PENDING)

    contractor: User = Relationship(back_populates="reward_requests")

class ProductType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: Optional[str] = None
    is_active: bool = Field(default=True)

    products: List["Product"] = Relationship(back_populates="product_type")

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    product_type_id: int = Field(foreign_key="producttype.id")
    unit: str # e.g. "Bag", "Ton", "Piece"
    price_per_unit: float = Field(default=0.0) # Product price per unit
    token_points_per_unit: float = Field(default=0.0) # Token points rewarded per unit
    image_url: Optional[str] = None # Optional product image URL
    is_active: bool = Field(default=True)

    product_type: ProductType = Relationship(back_populates="products")

class StaticContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True) # e.g. 'privacy_policy', 'terms_conditions', 'about_us'
    title: str
    content: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SupportStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class SupportTicket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    name: str
    email: str
    phone: Optional[str] = None
    subject: str
    message: str
    status: SupportStatus = Field(default=SupportStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FAQ(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str = Field(index=True)
    answer: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
