from typing import List
import logging
from sqlmodel import Session, select
from app.models import Notification, User, UserRole
from firebase_admin import messaging

def send_push_notification(session: Session, user_id: int, title: str, message_content: str):
    """Fetch user's fcm_token and trigger Firebase Push Notification."""
    user = session.get(User, user_id)
    if not user or not user.fcm_token or not user.fcm_token.strip():
        # Skip silently when FCM token is missing or empty
        return None

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message_content,
            ),
            token=user.fcm_token.strip()
        )
        response = messaging.send(message)
        logging.info(f"Successfully sent push notification to user {user_id}: {response}")
        return response
    except Exception as e:
        # Log as warning/error but do not raise it, ensuring API request does not fail
        logging.error(f"Error sending push notification to user {user_id}: {e}")
        return None

def create_notification(session: Session, user_id: int, title: str, message: str):
    """Create a notification for a specific user and add it to the session.
    The caller should commit the session after calling this function.
    """
    notif = Notification(user_id=user_id, title=title, message=message)
    session.add(notif)
    
    # Send push notification
    send_push_notification(session, user_id, title, message)
    
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
