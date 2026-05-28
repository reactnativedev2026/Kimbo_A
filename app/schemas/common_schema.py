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
