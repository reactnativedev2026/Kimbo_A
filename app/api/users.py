from app.schemas.user_schema import UserLogin
from app.utils.security import get_password_hash, verify_password 
from app.schemas.user_schema import UserListResponse
from app.schemas.user_schema import UserResponse
from app.schemas.user_schema import DeleteResponse
from ..schemas.user_schema import UserCreate, UserUpdate
from app.database import engine
from app.models import User
from app.database import create_db_and_tables
from fastapi import Depends, HTTPException, APIRouter
from typing import List
from sqlmodel import Session, select 

router = APIRouter()


@router.on_event("startup")
def on_startup():
    create_db_and_tables()
    
def get_session():
    with Session(engine) as session:
        yield session


@router.post("/", response_model=UserResponse)
def create_user(user_input: UserCreate, session: Session = Depends(get_session)):
    # YAHAN DHYAAN DEIN: UserCreate ko User model mein badalna zaruri hai
    db_user = User.model_validate(user_input)
    existing_user = session.exec(select(User).where(User.email == user_input.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user.password = get_password_hash(user_input.password)
    session.add(db_user) 
    session.commit()
    session.refresh(db_user)
    return {
        "status": "success",
        "message": f"User created successfully",
        "user_data": db_user
    }
@router.post("/login", response_model=UserResponse)
def login_user(login_data: UserLogin, session: Session = Depends(get_session)):
    # 1. Database mein user ko email se dhoondein
    user = session.exec(select(User).where(User.email == login_data.email)).first()
    
    # 2. Check karein ki user mila ya nahi, aur password sahi hai ya nahi
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # 3. Agar sab sahi hai toh success return karein
    return {
        "status": "success",
        "message": "Login successful",
        "user_data": user
    }
    
@router.get("/", response_model=UserListResponse)
def read_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all() # Saara data select karein
    return {
        "status": "success",
        "message": f"User list fetched successfully",
        "user_data": users
    }

@router.get("/{user_id}",  response_model=UserResponse)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "status": "success",
        "message": f"User fetched successfully",
        "user_data": user
    }


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdate, session: Session = Depends(get_session)):
    # 1. Purana user dhoondein
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    # 2. Jo data user ne bheja hai (sirf wahi update karein)
    new_data = user_data.model_dump(exclude_unset=True) # Sirf wahi fields jo bheje gaye hain
    for key, value in new_data.items():
        setattr(db_user, key, value) # Purane data ko badlein
    # 3. Save karein
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {
        "status": "success",
        "message": f"User updated successfully",
        "user_data": db_user
    }

@router.delete("/{user_id}", response_model=DeleteResponse)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    # 1. Purana user dhoondein
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    # 2. Delete karein
    session.delete(db_user)
    session.commit()
    return {
        "status": "success",
        "message": f"User with ID {user_id} has been deleted successfully",
        "deleted_id": user_id
    }

