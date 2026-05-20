from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import engine
from app.models import User, UserRole, MaterialTransfer, PurchaseEntry, Scheme, RewardRedeem
from app.schemas.app_schemas import AdminDashboardStats, ContractorDashboardStats
from app.api.users import get_current_user

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.get("/admin", response_model=AdminDashboardStats)
def get_admin_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    total_contractors = len(session.exec(select(User).where(User.role == UserRole.CONTRACTOR)).all())
    total_transfers = len(session.exec(select(MaterialTransfer)).all())
    total_redeemed = len(session.exec(select(RewardRedeem)).all())
    active_schemes = len(session.exec(select(Scheme).where(Scheme.is_active == True)).all())

    return {
        "total_contractors": total_contractors,
        "total_material_transfers": total_transfers,
        "total_redeemed_rewards": total_redeemed,
        "active_schemes": active_schemes
    }

@router.get("/contractor", response_model=ContractorDashboardStats)
def get_contractor_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CONTRACTOR:
        raise HTTPException(status_code=403, detail="Contractor access required")

    total_purchases = len(session.exec(select(PurchaseEntry).where(PurchaseEntry.contractor_id == current_user.id)).all())
    pending_redeems = len(session.exec(select(RewardRedeem).where(
        RewardRedeem.contractor_id == current_user.id,
        RewardRedeem.status == "pending"
    )).all())

    return {
        "total_tokens": current_user.total_tokens,
        "total_purchases": total_purchases,
        "pending_redeems": pending_redeems
    }
