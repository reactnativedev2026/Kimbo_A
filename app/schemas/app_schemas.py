from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import RedeemStatus

# Material Transfer Schemas
class ContractorDetail(SQLModel):
    id: int
    full_name: str
    mobile_number: Optional[str] = None
    contractor_code: Optional[str] = None
    address: Optional[str] = None

class MaterialTransferBase(SQLModel):
    transfer_id: str
    contractor_id: int
    material_type: str
    quantity: float
    unit: str
    vehicle_number: Optional[str] = None
    driver_details: Optional[str] = None
    notes: Optional[str] = None

class MaterialTransferCreate(MaterialTransferBase):
    pass

class MaterialTransferRead(MaterialTransferBase):
    id: int
    date: datetime
    created_at: datetime
    updated_at: datetime

class MaterialTransferResponse(SQLModel):
    status: str
    message: str
    data: MaterialTransferRead

# Purchase Entry Schemas
from app.models import PurchaseStatus

class PurchaseEntryBase(SQLModel):
    product_id: int
    quantity_bought: float
    bill_number: Optional[str] = None

class PurchaseEntryCreate(PurchaseEntryBase):
    pass

class PurchaseEntryRead(PurchaseEntryBase):
    id: int
    contractor_id: int
    date: datetime
    status: PurchaseStatus
    tokens_earned: int
    total_amount: float
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ProductDetail(SQLModel):
    id: int
    name: str
    description: Optional[str] = None
    unit: str
    price_per_unit: float
    token_points_per_unit: float
    image_url: Optional[str] = None

class PurchaseEntryWithProductRead(PurchaseEntryRead):
    product: Optional[ProductDetail] = None

class PurchaseEntryAdminRead(PurchaseEntryRead):
    product: Optional[ProductDetail] = None
    contractor: Optional[ContractorDetail] = None

class PurchaseEntryResponse(SQLModel):
    status: str
    message: str
    data: PurchaseEntryRead
    bill_html: Optional[str] = None
    pdf_url: Optional[str] = None

class PurchaseEntryWithProductResponse(SQLModel):
    status: str
    message: str
    data: PurchaseEntryWithProductRead
    bill_html: Optional[str] = None
    pdf_url: Optional[str] = None

class PurchaseEntryAdminResponse(SQLModel):
    status: str
    message: str
    data: PurchaseEntryAdminRead
    bill_html: Optional[str] = None
    pdf_url: Optional[str] = None

# Scheme Schemas
class SchemeBase(SQLModel):
    title: str
    description: str
    start_date: datetime
    end_date: datetime
    tokens_required: int = 0
    banner_image: Optional[str] = None
    is_active: bool = True

class SchemeCreate(SchemeBase):
    pass

class SchemeRead(SchemeBase):
    id: int
    created_at: datetime
    updated_at: datetime

class SchemeUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tokens_required: Optional[int] = None
    banner_image: Optional[str] = None
    is_active: Optional[bool] = None

class SchemeResponse(SQLModel):
    status: str
    message: str
    data: SchemeRead

# Reward Redeem Schemas
class RewardRedeemBase(SQLModel):
    tokens_used: int
    reward_description: str
    scheme_id: Optional[int] = None

class RewardRedeemCreate(SQLModel):
    scheme_id: int

class RewardRedeemRead(RewardRedeemBase):
    id: int
    contractor_id: int
    date: datetime
    status: RedeemStatus
    created_at: datetime
    updated_at: datetime
    
    scheme: Optional[SchemeRead] = None
    contractor: Optional[ContractorDetail] = None

class RewardRedeemResponse(SQLModel):
    status: str
    message: str
    data: RewardRedeemRead

# Dashboard Schemas
class EarningChartItem(SQLModel):
    label: str
    amount: float

class RecentPurchaseItem(SQLModel):
    id: int
    contractor_name: str
    product_name: str
    quantity_bought: float
    total_amount: float
    tokens_earned: int
    status: str
    bill_number: Optional[str] = None
    date: datetime

class AdminDashboardStats(SQLModel):
    total_contractors: int
    total_approved_purchases: int
    total_redeemed_rewards: int
    active_schemes: int
    daily_earnings: List[EarningChartItem] = []
    weekly_earnings: List[EarningChartItem] = []
    monthly_earnings: List[EarningChartItem] = []
    recent_purchases: List[RecentPurchaseItem] = []

class ContractorDashboardStats(SQLModel):
    total_tokens: int
    total_purchases: int
    pending_redeems: int

# Earning History Schemas
class EarningHistoryItem(SQLModel):
    id: int
    type: str  # "purchase" or "admin"
    points: int
    date: datetime
    description: str
    ref_id: Optional[int] = None
    bill_number: Optional[str] = None
    product_name: Optional[str] = None

class EarningHistoryResponse(SQLModel):
    status: str
    message: str
    total_earned: int
    data: List[EarningHistoryItem]

