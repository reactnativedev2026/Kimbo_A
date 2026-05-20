from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.database import engine
from app.models import PurchaseEntry, User, Product, PurchaseStatus
from app.schemas.app_schemas import PurchaseEntryCreate, PurchaseEntryResponse, PurchaseEntryRead
from app.api.users import get_current_admin, get_current_contractor

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

# ==============================
# CONTRACTOR APIs
# ==============================
@router.post("/contractor", response_model=PurchaseEntryResponse)
def add_purchase_contractor(
    purchase_data: PurchaseEntryCreate, 
    session: Session = Depends(get_session),
    contractor_user: User = Depends(get_current_contractor)
):
    if purchase_data.contractor_id != contractor_user.id:
        raise HTTPException(status_code=403, detail="Can only add purchases for yourself")

    # Verify product
    product = session.get(Product, purchase_data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Tokens are calculated based on token_points_per_unit * quantity
    tokens_calculated = int(product.token_points_per_unit * purchase_data.quantity_bought)
    
    db_purchase = PurchaseEntry.model_validate(purchase_data)
    db_purchase.status = PurchaseStatus.PENDING
    db_purchase.tokens_earned = tokens_calculated  # Record but don't give them yet
    
    session.add(db_purchase)
    session.commit()
    session.refresh(db_purchase)

    return {
        "status": "success",
        "message": f"Purchase recorded. {tokens_calculated} tokens are pending admin approval.",
        "data": db_purchase
    }

@router.get("/contractor", response_model=List[PurchaseEntryRead])
def get_purchases_contractor(
    session: Session = Depends(get_session),
    contractor_user: User = Depends(get_current_contractor)
):
    purchases = session.exec(select(PurchaseEntry).where(PurchaseEntry.contractor_id == contractor_user.id)).all()
    return purchases

# ==============================
# ADMIN APIs
# ==============================
@router.get("/admin", response_model=List[PurchaseEntryRead])
def get_purchases_admin(
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    purchases = session.exec(select(PurchaseEntry)).all()
    return purchases

@router.patch("/admin/{purchase_id}/status", response_model=PurchaseEntryResponse)
def update_purchase_status(
    purchase_id: int,
    status: PurchaseStatus,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    db_purchase = session.get(PurchaseEntry, purchase_id)
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase entry not found")

    if db_purchase.status == PurchaseStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Purchase is already approved.")

    db_purchase.status = status
    
    if status == PurchaseStatus.APPROVED:
        # Give tokens to the contractor
        contractor = session.get(User, db_purchase.contractor_id)
        if contractor:
            contractor.total_tokens += db_purchase.tokens_earned
            session.add(contractor)

    session.add(db_purchase)
    session.commit()
    session.refresh(db_purchase)

    return {
        "status": "success",
        "message": f"Purchase status updated to {status}",
        "data": db_purchase
    }
