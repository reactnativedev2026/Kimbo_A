from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import EmailStr       
from app.models import UserRole, UserStatus

class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr 
    full_name: Optional[str] = Field(default=None,min_length=2)
    role: UserRole = Field(default=UserRole.CONTRACTOR)
    contractor_code: Optional[str] = None
    mobile_number: Optional[str] = None
    address: Optional[str] = None
    gst_details: Optional[str] = None
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    profile_image: Optional[str] = None
    govt_id: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(min_length=6)

class UserRead(UserBase):
    id: int
    total_tokens: int
    fcm_token: Optional[str] = None
    device_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UserUpdate(SQLModel):
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    address: Optional[str] = None
    gst_details: Optional[str] = None
    status: Optional[UserStatus] = None
    profile_image: Optional[str] = None
    govt_id: Optional[str] = None

class UserResponse(SQLModel):
    status: str
    message: str
    user_data: UserRead

class UserListResponse(SQLModel):
    status: str
    message: str
    user_data: list[UserRead]

class DeleteResponse(SQLModel):
    status: str
    message: str
    deleted_id: int
    
class UserLoginResponse(SQLModel):
    status: str
    message: str
    access_token: str
    token_type: str = "bearer"
    user_data: UserRead
    
class UserLogin(SQLModel):
    email: EmailStr
    password: str
    fcm_token: Optional[str] = None
    device_type: Optional[str] = None