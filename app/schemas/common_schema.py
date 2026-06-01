from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime
from app.models import SupportStatus

# Static Content Schemas
class StaticContentCreate(SQLModel):
    key: str
    title: str
    content: str

class StaticContentUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None

class StaticContentRead(SQLModel):
    id: int
    key: str
    title: str
    content: str
    updated_at: datetime

class StaticContentResponse(SQLModel):
    status: str
    message: str
    data: StaticContentRead


# Support Ticket Schemas
class SupportTicketCreate(SQLModel):
    user_id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    subject: str
    message: str

class SupportTicketRead(SQLModel):
    id: int
    user_id: Optional[int]
    name: str
    email: str
    phone: Optional[str]
    subject: str
    message: str
    status: SupportStatus
    created_at: datetime

class SupportTicketStatusUpdate(SQLModel):
    status: SupportStatus

class SupportTicketResponse(SQLModel):
    status: str
    message: str
    data: SupportTicketRead

# FAQ Schemas
class FAQCreate(SQLModel):
    question: str
    answer: str
    is_active: Optional[bool] = True

class FAQUpdate(SQLModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    is_active: Optional[bool] = None

class FAQRead(SQLModel):
    id: int
    question: str
    answer: str
    is_active: bool
    created_at: datetime

class FAQResponse(SQLModel):
    status: str
    message: str
    data: FAQRead

class FAQListResponse(SQLModel):
    status: str
    message: str
    data: list[FAQRead]
