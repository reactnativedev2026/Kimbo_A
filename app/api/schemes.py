from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.database import engine, get_session
from app.models import Scheme, User, UserRole, UserStatus
from app.schemas.app_schemas import SchemeCreate, SchemeResponse, SchemeRead
from app.api.users import get_current_user
from app.utils.notifications import create_notification

router = APIRouter()

@router.post("/", response_model=SchemeResponse)
def create_scheme(
    scheme_data: SchemeCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create schemes")
    
    db_scheme = Scheme.model_validate(scheme_data)
    session.add(db_scheme)
    session.commit()
    session.refresh(db_scheme)

    # Notify all active contractors about the new scheme
    contractors = session.exec(select(User).where(User.role == UserRole.CONTRACTOR, User.status == UserStatus.ACTIVE)).all()
    for contractor in contractors:
        create_notification(
            session,
            contractor.id,
            "New Scheme Available!",
            f"A new scheme '{db_scheme.title}' has been launched."
        )
    if contractors:
        session.commit()

    return {
        "status": "success",
        "message": "Scheme created successfully",
        "data": db_scheme
    }

@router.get("/", response_model=List[SchemeRead])
def get_schemes(
    session: Session = Depends(get_session)
):
    # Any authenticated user can view schemes (or we can make it public)
    schemes = session.exec(select(Scheme).where(Scheme.is_active == True)).all()
    return schemes
