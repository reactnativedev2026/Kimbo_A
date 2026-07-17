from sqlmodel import SQLModel
from typing import List, Optional
from datetime import datetime

class NotificationRead(SQLModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: Optional[str] = None
    related_id: Optional[int] = None
    is_read: bool
    created_at: datetime

class NotificationListResponse(SQLModel):
    status: str
    message: str
    data: List[NotificationRead]
    unread_count: int

class NotificationTestRequest(SQLModel):
    fcm_token: str
    title: str
    message: str
    notification_type: Optional[str] = None
    related_id: Optional[int] = None

class NotificationTestResponse(SQLModel):
    status: str
    message: str
    fcm_response: Optional[str] = None
