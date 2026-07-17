from typing import List
import logging
from sqlmodel import Session, select
from app.models import Notification, User, UserRole
from firebase_admin import messaging

def send_push_notification_to_token(token: str, title: str, message_content: str, notification_type: str = None, related_id: int = None):
    """Send an FCM push notification directly to the provided token."""
    if not token or not token.strip():
        return None

    try:
        data_payload = {}
        if notification_type:
            data_payload["type"] = str(notification_type)
        if related_id is not None:
            data_payload["related_id"] = str(related_id)

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message_content,
            ),
            data=data_payload if data_payload else None,
            token=token.strip()
        )
        response = messaging.send(message)
        logging.info(f"Successfully sent push notification to token: {response}")
        return response
    except Exception as e:
        logging.error(f"Error sending push notification to token: {e}")
        return None


def send_push_notification(session: Session, user_id: int, title: str, message_content: str, notification_type: str = None, related_id: int = None):
    """Fetch user's fcm_token and trigger Firebase Push Notification."""
    user = session.get(User, user_id)
    if not user or not user.fcm_token or not user.fcm_token.strip():
        # Skip silently when FCM token is missing or empty
        return None

    try:
        data_payload = {}
        if notification_type:
            data_payload["type"] = str(notification_type)
        if related_id is not None:
            data_payload["related_id"] = str(related_id)

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message_content,
            ),
            data=data_payload if data_payload else None,
            token=user.fcm_token.strip()
        )
        response = messaging.send(message)
        logging.info(f"Successfully sent push notification to user {user_id}: {response}")
        return response
    except Exception as e:
        # Log as warning/error but do not raise it, ensuring API request does not fail
        logging.error(f"Error sending push notification to user {user_id}: {e}")
        return None

def create_notification(session: Session, user_id: int, title: str, message: str, notification_type: str = None, related_id: int = None):
    """Create a notification for a specific user and add it to the session.
    The caller should commit the session after calling this function.
    """
    notif = Notification(
        user_id=user_id, 
        title=title, 
        message=message, 
        notification_type=notification_type, 
        related_id=related_id
    )
    session.add(notif)
    
    # Send push notification
    send_push_notification(session, user_id, title, message, notification_type, related_id)
    
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
