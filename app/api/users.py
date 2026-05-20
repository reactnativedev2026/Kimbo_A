from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables, get_session
from app.models import User, UserRole
from app.schemas.user_schema import (
    UserCreate,
    UserLogin,
    UserLoginResponse,
    UserResponse,
    UserListResponse,
    DeleteResponse,
    UserUpdate,
)
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
    existing_user = session.exec(select(User).where(User.email == user_input.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user.password = get_password_hash(user_input.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {"status": "success", "message": "Admin registered successfully", "user_data": db_user}

@router.post("/admin/add-contractor", response_model=UserResponse)
def add_contractor(
    user_input: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    db_user = User.model_validate(user_input)
    db_user.role = UserRole.CONTRACTOR
    existing_user = session.exec(select(User).where(User.email == user_input.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user.password = get_password_hash(user_input.password)
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
def list_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return {"status": "success", "message": "User list fetched successfully", "user_data": users}

@router.get("/admin/contractors", response_model=UserListResponse)
def list_contractors(
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin),
):
    contractors = session.exec(select(User).where(User.role == UserRole.CONTRACTOR)).all()
    return {"status": "success", "message": "Contractors list fetched successfully", "user_data": contractors}

from pydantic import BaseModel
class AddPointsRequest(BaseModel):
    points: int

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
    session.add(contractor)
    session.commit()
    session.refresh(contractor)
    return {
        "status": "success",
        "message": f"{request.points} points manually added to contractor",
        "user_data": contractor,
    }

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