from sqlmodel import SQLModel
from typing import List, Optional
from datetime import datetime

class NotificationRead(SQLModel):
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime

class NotificationListResponse(SQLModel):
    status: str
    message: str
    data: List[NotificationRead]
    unread_count: int
