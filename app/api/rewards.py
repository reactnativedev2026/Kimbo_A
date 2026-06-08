from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.database import engine, get_session
from app.models import RewardRedeem, User, UserRole, RedeemStatus, Scheme
from app.schemas.app_schemas import RewardRedeemCreate, RewardRedeemResponse, RewardRedeemRead
from app.api.users import get_current_user
from app.utils.notifications import create_notification

router = APIRouter()

@router.post("/redeem", response_model=RewardRedeemResponse)
def request_redeem(
    redeem_data: RewardRedeemCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CONTRACTOR:
        raise HTTPException(status_code=403, detail="Only contractors can request reward redemptions")

    scheme = session.get(Scheme, redeem_data.scheme_id)
    if not scheme or not scheme.is_active:
        raise HTTPException(status_code=404, detail="Scheme not found or inactive")
        
    if current_user.total_tokens < scheme.tokens_required:
        raise HTTPException(status_code=400, detail="Insufficient tokens")

    # Deduct tokens
    current_user.total_tokens -= scheme.tokens_required
    
    db_redeem = RewardRedeem(
        contractor_id=current_user.id,
        scheme_id=scheme.id,
        tokens_used=scheme.tokens_required,
        reward_description=scheme.title,
    )
    
    session.add(db_redeem)
    session.add(current_user)
    session.commit()
    session.refresh(db_redeem)
    
    create_notification(
        session,
        current_user.id,
        "Reward Request Submitted",
        f"Your request to redeem '{scheme.title}' has been submitted successfully."
    )
    session.commit()

    # Explicitly assign scheme and contractor to prevent lazy loading serialization issues outside the session
    db_redeem.scheme = scheme
    db_redeem.contractor = current_user

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

    create_notification(
        session,
        db_redeem.contractor_id,
        "Reward Request Updated",
        f"Your reward request for '{db_redeem.reward_description}' has been {status}."
    )
    session.commit()

    # Explicitly assign scheme and contractor to prevent lazy loading serialization issues
    db_redeem.scheme = session.get(Scheme, db_redeem.scheme_id) if db_redeem.scheme_id else None
    db_redeem.contractor = session.get(User, db_redeem.contractor_id) if db_redeem.contractor_id else None

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
        redeems = session.exec(select(RewardRedeem).order_by(RewardRedeem.created_at.desc())).all()
    else:
        redeems = session.exec(select(RewardRedeem).where(RewardRedeem.contractor_id == current_user.id).order_by(RewardRedeem.created_at.desc())).all()
    return redeems
