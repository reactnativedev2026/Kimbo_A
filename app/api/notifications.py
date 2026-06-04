from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import engine, get_session
from app.utils.notifications import get_notifications, mark_notification_as_read, create_notification
from app.models import Notification
from app.schemas.notification_schema import NotificationListResponse, NotificationRead
from app.api.users import get_current_user

router = APIRouter()

@router.get("/", response_model=NotificationListResponse, summary="List notifications", tags=["notifications"])
def list_notifications(
    only_unread: bool = False,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    notifications = get_notifications(session, current_user.id, only_unread)
    # Compute unread count
    unread_query = select(Notification).where(Notification.user_id == current_user.id, Notification.is_read == False)
    unread_count = len(session.exec(unread_query).all())
    # Convert to response schema
    notification_reads = [NotificationRead(**(n.model_dump() if hasattr(n, 'model_dump') else n.dict())) for n in notifications]
    return NotificationListResponse(
        status="success",
        message="Notifications fetched",
        data=notification_reads,
        unread_count=unread_count,
    )

@router.patch("/{notification_id}/read", response_model=NotificationRead, summary="Mark notification as read", tags=["notifications"])
def read_notification(
    notification_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    notif = mark_notification_as_read(session, notification_id, current_user.id)
    session.commit()
    session.refresh(notif)
    return notif

@router.post("/read-all", response_model=NotificationListResponse, summary="Mark all notifications as read", tags=["notifications"])
def read_all_notifications(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    # Mark all as read
    notifications = session.exec(select(Notification).where(Notification.user_id == current_user.id)).all()
    for n in notifications:
        if not n.is_read:
            n.is_read = True
            session.add(n)
    session.commit()
    
    updated_notifications = get_notifications(session, current_user.id)
    notification_reads = [NotificationRead(**(n.model_dump() if hasattr(n, 'model_dump') else n.dict())) for n in updated_notifications]
    return NotificationListResponse(
        status="success",
        message="All notifications marked as read",
        data=notification_reads,
        unread_count=0,
    )
