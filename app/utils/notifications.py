from typing import List
from sqlmodel import Session, select
from app.models import Notification, User, UserRole

def create_notification(session: Session, user_id: int, title: str, message: str):
    """Create a notification for a specific user and add it to the session.
    The caller should commit the session after calling this function.
    """
    notif = Notification(user_id=user_id, title=title, message=message)
    session.add(notif)
    # Do not commit here; let the caller handle transaction.
    return notif

def get_user_notifications(session: Session, user_id: int) -> List[Notification]:
    """Return all notifications for the given user ordered by newest first."""
    return session.exec(
        select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
    ).all()

def get_notifications(session: Session, user_id: int, only_unread: bool = False) -> List[Notification]:
    """Return notifications for a user, optionally filtering to only unread ones."""
    query = select(Notification).where(Notification.user_id == user_id)
    if only_unread:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc())
    return session.exec(query).all()

def mark_notification_as_read(session: Session, notification_id: int, user_id: int):
    notif = session.get(Notification, notification_id)
    if not notif or notif.user_id != user_id:
        raise ValueError("Notification not found or access denied")
    notif.is_read = True
    session.add(notif)
    return notif
