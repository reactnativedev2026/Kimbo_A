import os
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from sqlalchemy import func
from pydantic import BaseModel

from app.database import engine, create_db_and_tables, get_session
from app.models import User, UserRole, UserStatus, MaterialTransfer, PurchaseEntry, RewardRedeem, AdminPointAdjustment, Product, PurchaseStatus
from app.schemas.user_schema import (
    UserCreate,
    ContractorCreate,
    UserLogin,
    UserLoginResponse,
    UserResponse,
    UserListResponse,
    PaginatedUserListResponse,
    DeleteResponse,
    UserUpdate,
)
from app.schemas.app_schemas import EarningHistoryResponse, EarningHistoryItem

from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)

router = APIRouter()

security = HTTPBearer()

@router.on_event("startup")
def on_startup():
    create_db_and_tables()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Token payload is invalid")
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="User account is inactive. Access denied.")
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    return current_user

def get_current_contractor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.CONTRACTOR:
        raise HTTPException(status_code=403, detail="Access denied. Contractor role required.")
    return current_user

# -------------------- Admin Endpoints --------------------
@router.post("/admin/register", response_model=UserResponse)
def register_admin(user_input: UserCreate, session: Session = Depends(get_session)):
    db_user = User.model_validate(user_input)
    db_user.role = UserRole.ADMIN  # Force role to ADMIN
    
    # Check if email is already registered
    existing_user = session.exec(select(User).where(User.email == user_input.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Check if username is already registered
    existing_username = session.exec(select(User).where(User.username == user_input.username)).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # Check if contractor_code is already registered
    if user_input.contractor_code is not None:
        existing_code = session.exec(select(User).where(User.contractor_code == user_input.contractor_code)).first()
        if existing_code:
            raise HTTPException(status_code=400, detail="Contractor code already registered")
        
    db_user.password = get_password_hash(user_input.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {"status": "success", "message": "Admin registered successfully", "user_data": db_user}

@router.post("/admin/add-contractor", response_model=UserResponse)
def add_contractor(
    contractor_input: ContractorCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    # Check if email is already registered
    existing_user = session.exec(select(User).where(User.email == contractor_input.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        email=contractor_input.email,
        username=contractor_input.email,
        full_name=contractor_input.email,
        password=get_password_hash(contractor_input.password),
        role=UserRole.CONTRACTOR,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {"status": "success", "message": "Contractor added successfully", "user_data": db_user}

# -------------------- Authentication --------------------
@router.post("/auth/login", response_model=UserLoginResponse)
def login_user(login_data: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == login_data.email)).first()
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="User account is inactive. Login denied.")
        
    # Update FCM token and device type if provided
    updated = False
    if login_data.fcm_token is not None:
        user.fcm_token = login_data.fcm_token
        updated = True
    if login_data.device_type is not None:
        user.device_type = login_data.device_type
        updated = True
        
    if updated:
        session.add(user)
        session.commit()
        session.refresh(user)
        
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {
        "status": "success",
        "message": f"{user.role.value.capitalize()} Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_data": user,
    }

# -------------------- User Management --------------------
@router.get("/list", response_model=UserListResponse)
def list_users(
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin),
):
    users = session.exec(select(User)).all()
    return {"status": "success", "message": "User list fetched successfully", "user_data": users}

@router.get("/admin/contractors", response_model=UserListResponse)
def list_contractors(
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin),
):
    contractors = session.exec(select(User).where(User.role == UserRole.CONTRACTOR)).all()
    return {
        "status": "success",
        "message": "Contractors list fetched successfully",
        "user_data": contractors,
    }

@router.get("/admin/admins", response_model=UserListResponse)
def list_admins(
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin),
):
    admins = session.exec(select(User).where(User.role == UserRole.ADMIN)).all()
    return {"status": "success", "message": "Admins list fetched successfully", "user_data": admins}

class AddPointsRequest(BaseModel):
    points: int
    notes: Optional[str] = None

@router.post("/admin/contractors/{contractor_id}/add-points", response_model=UserResponse)
def add_points_to_contractor(
    contractor_id: int,
    request: AddPointsRequest,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin),
):
    contractor = session.get(User, contractor_id)
    if not contractor or contractor.role != UserRole.CONTRACTOR:
        raise HTTPException(status_code=404, detail="Contractor not found")
    contractor.total_tokens += request.points
    # Log the point adjustment
    adjustment = AdminPointAdjustment(
        contractor_id=contractor_id,
        points=request.points,
        notes=request.notes
    )
    session.add(contractor)
    session.add(adjustment)
    # Send notification to contractor
    from app.utils.notifications import create_notification
    create_notification(session, contractor_id, "Points Added", f"{request.points} points added by admin. {request.notes or ''}")
    session.commit()
    session.refresh(contractor)
    return {
        "status": "success",
        "message": f"{request.points} points manually added to contractor",
        "user_data": contractor,
    }


@router.get("/admin/contractors/{contractor_id}/detail")
def get_contractor_detail(
    contractor_id: int,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin),
):
    contractor = session.get(User, contractor_id)
    if not contractor or contractor.role != UserRole.CONTRACTOR:
        raise HTTPException(status_code=404, detail="Contractor not found")
        
    # Get transfers
    transfers = session.exec(select(MaterialTransfer).where(MaterialTransfer.contractor_id == contractor_id)).all()
    
    # Get rewards
    rewards = session.exec(select(RewardRedeem).where(RewardRedeem.contractor_id == contractor_id)).all()
    
    # Get purchases
    purchases = session.exec(select(PurchaseEntry).where(PurchaseEntry.contractor_id == contractor_id)).all()
    
    # Create recent activity by combining purchases, transfers, and rewards, sorted by date descending.
    recent_activity = []
    
    for p in purchases:
        recent_activity.append({
            "type": "purchase",
            "id": p.id,
            "date": p.date,
            "description": f"Bought product ID {p.product_id} (qty: {p.quantity_bought})",
            "amount": p.total_amount,
            "tokens_earned": p.tokens_earned,
            "status": p.status
        })
        
    for t in transfers:
        recent_activity.append({
            "type": "transfer",
            "id": t.id,
            "date": t.date,
            "description": f"Transferred {t.material_type} (qty: {t.quantity} {t.unit})",
            "amount": 0.0,
            "tokens_earned": 0,
            "status": "approved"
        })
        
    for r in rewards:
        recent_activity.append({
            "type": "reward_redeem",
            "id": r.id,
            "date": r.date,
            "description": f"Redeemed reward: {r.reward_description}",
            "amount": 0.0,
            "tokens_earned": -r.tokens_used,
            "status": r.status
        })
        
    # Sort recent activity by date descending
    recent_activity.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "status": "success",
        "message": "Contractor details fetched successfully",
        "data": {
            "contractor": contractor,
            "transfers": transfers,
            "rewards": rewards,
            "recent_activity": recent_activity
        }
    }

@router.patch("/profile/update", response_model=UserResponse)
def update_profile(
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    new_data = user_data.model_dump(exclude_unset=True)
    for key, value in new_data.items():
        setattr(current_user, key, value)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return {"status": "success", "message": "Profile updated successfully", "user_data": current_user}

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {"status": "success", "message": "User profile fetched successfully", "user_data": current_user}

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "message": "User fetched successfully", "user_data": user}

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    new_data = user_data.model_dump(exclude_unset=True)
    for key, value in new_data.items():
        setattr(db_user, key, value)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {"status": "success", "message": "User updated successfully", "user_data": db_user}

@router.delete("/{user_id}", response_model=DeleteResponse)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(db_user)
    session.commit()
    return {"status": "success", "message": f"User with ID {user_id} has been deleted successfully", "deleted_id": user_id}

# -------------------- Earning Point History --------------------
def get_contractor_earning_history(contractor_id: int, session: Session):
    # 1. Fetch approved purchases along with product details
    purchases_q = select(PurchaseEntry, Product).join(
        Product, PurchaseEntry.product_id == Product.id
    ).where(
        PurchaseEntry.contractor_id == contractor_id,
        PurchaseEntry.status == PurchaseStatus.APPROVED
    )
    purchases = session.exec(purchases_q).all()
    
    # 2. Fetch admin manual point adjustments
    adjustments = session.exec(
        select(AdminPointAdjustment).where(AdminPointAdjustment.contractor_id == contractor_id)
    ).all()
    
    history_items = []
    total_earned = 0
    
    for purchase, product in purchases:
        history_items.append(EarningHistoryItem(
            id=purchase.id,
            type="purchase",
            points=purchase.tokens_earned,
            date=purchase.date,
            description=f"Points earned from purchase of {product.name}",
            ref_id=purchase.id,
            bill_number=purchase.bill_number,
            product_name=product.name
        ))
        total_earned += purchase.tokens_earned
        
    for adj in adjustments:
        history_items.append(EarningHistoryItem(
            id=adj.id,
            type="admin",
            points=adj.points,
            date=adj.created_at,
            description=adj.notes or "Manually added by Admin",
            ref_id=adj.id
        ))
        if adj.points > 0:
            total_earned += adj.points

    # Sort history items by date descending
    history_items.sort(key=lambda x: x.date, reverse=True)
    
    return {
        "status": "success",
        "message": "Earning point history fetched successfully",
        "total_earned": total_earned,
        "data": history_items
    }

@router.get("/me/earning-history", response_model=EarningHistoryResponse)
def get_my_earning_history(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_contractor),
):
    return get_contractor_earning_history(current_user.id, session)

@router.get("/admin/contractors/{contractor_id}/earning-history", response_model=EarningHistoryResponse)
def get_contractor_earning_history_admin(
    contractor_id: int,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin),
):
    contractor = session.get(User, contractor_id)
    if not contractor or contractor.role != UserRole.CONTRACTOR:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return get_contractor_earning_history(contractor_id, session)
