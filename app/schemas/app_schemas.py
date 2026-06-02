from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import RedeemStatus

# Material Transfer Schemas
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

class PurchaseEntryResponse(SQLModel):
    status: str
    message: str
    data: PurchaseEntryRead
    bill_html: Optional[str] = None

# Scheme Schemas
class SchemeBase(SQLModel):
    title: str
    description: str
    start_date: datetime
    end_date: datetime
    banner_image: Optional[str] = None
    is_active: bool = True

class SchemeCreate(SchemeBase):
    pass

class SchemeRead(SchemeBase):
    id: int
    created_at: datetime
    updated_at: datetime

class SchemeResponse(SQLModel):
    status: str
    message: str
    data: SchemeRead

# Reward Redeem Schemas
class RewardRedeemBase(SQLModel):
    tokens_used: int
    reward_description: str

class RewardRedeemCreate(RewardRedeemBase):
    contractor_id: int

class RewardRedeemRead(RewardRedeemBase):
    id: int
    contractor_id: int
    date: datetime
    status: RedeemStatus
    created_at: datetime
    updated_at: datetime

class RewardRedeemResponse(SQLModel):
    status: str
    message: str
    data: RewardRedeemRead

# Dashboard Schemas
class AdminDashboardStats(SQLModel):
    total_contractors: int
    total_material_transfers: int
    total_redeemed_rewards: int
    active_schemes: int

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

