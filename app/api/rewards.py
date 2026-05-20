from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.database import engine
from app.models import RewardRedeem, User, UserRole, RedeemStatus
from app.schemas.app_schemas import RewardRedeemCreate, RewardRedeemResponse, RewardRedeemRead
from app.api.users import get_current_user

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/redeem", response_model=RewardRedeemResponse)
def request_redeem(
    redeem_data: RewardRedeemCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CONTRACTOR:
        raise HTTPException(status_code=403, detail="Only contractors can request reward redemptions")

    if redeem_data.contractor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot request redeem for another user")
        
    if current_user.total_tokens < redeem_data.tokens_used:
        raise HTTPException(status_code=400, detail="Insufficient tokens")

    # Deduct tokens
    current_user.total_tokens -= redeem_data.tokens_used
    
    db_redeem = RewardRedeem.model_validate(redeem_data)
    
    session.add(db_redeem)
    session.add(current_user)
    session.commit()
    session.refresh(db_redeem)

    return {
        "status": "success",
        "message": "Reward redemption requested successfully",
        "data": db_redeem
    }

@router.patch("/{redeem_id}/status", response_model=RewardRedeemResponse)
def update_redeem_status(
    redeem_id: int, 
    status: RedeemStatus, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update redeem status")

    db_redeem = session.get(RewardRedeem, redeem_id)
    if not db_redeem:
        raise HTTPException(status_code=404, detail="Redeem request not found")

    if status == RedeemStatus.REJECTED and db_redeem.status != RedeemStatus.REJECTED:
        # Refund tokens
        contractor = session.get(User, db_redeem.contractor_id)
        if contractor:
            contractor.total_tokens += db_redeem.tokens_used
            session.add(contractor)

    db_redeem.status = status
    session.add(db_redeem)
    session.commit()
    session.refresh(db_redeem)

    return {
        "status": "success",
        "message": f"Redeem status updated to {status}",
        "data": db_redeem
    }

@router.get("/", response_model=List[RewardRedeemRead])
def get_redeems(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN:
        redeems = session.exec(select(RewardRedeem)).all()
    else:
        redeems = session.exec(select(RewardRedeem).where(RewardRedeem.contractor_id == current_user.id)).all()
    return redeems
