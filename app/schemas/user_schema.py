from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import EmailStr       

class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr 
    full_name: Optional[str] = Field(default=None,min_length=2)

class UserCreate(UserBase):
    password: str = Field(min_length=6)

class UserRead(UserBase):
    id: int

class UserUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    # password: Optional[str] = None

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
    
class UserLogin(SQLModel):
    email: EmailStr
    password: str