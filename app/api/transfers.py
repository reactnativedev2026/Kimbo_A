from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.database import engine
from app.models import MaterialTransfer, User
from app.schemas.app_schemas import MaterialTransferCreate, MaterialTransferResponse, MaterialTransferRead
from app.api.users import get_current_admin, get_current_contractor

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

# ==============================
# ADMIN APIs
# ==============================
@router.post("/admin", response_model=MaterialTransferResponse)
def create_transfer_admin(
    transfer_data: MaterialTransferCreate, 
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    contractor = session.get(User, transfer_data.contractor_id)
    if not contractor or contractor.role.value != "contractor":
        raise HTTPException(status_code=404, detail="Contractor not found")

    db_transfer = MaterialTransfer.model_validate(transfer_data)
    session.add(db_transfer)
    session.commit()
    session.refresh(db_transfer)

    return {
        "status": "success",
        "message": "Material transfer recorded successfully",
        "data": db_transfer
    }

@router.get("/admin", response_model=List[MaterialTransferRead])
def get_transfers_admin(
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    transfers = session.exec(select(MaterialTransfer)).all()
    return transfers

# ==============================
# CONTRACTOR APIs
# ==============================
@router.get("/contractor", response_model=List[MaterialTransferRead])
def get_transfers_contractor(
    session: Session = Depends(get_session),
    contractor_user: User = Depends(get_current_contractor)
):
    transfers = session.exec(select(MaterialTransfer).where(MaterialTransfer.contractor_id == contractor_user.id).all())
    return transfers
