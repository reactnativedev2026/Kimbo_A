from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from app.database import engine
from app.models import StaticContent, SupportTicket, User, UserRole, SupportStatus
from app.schemas.common_schema import (
    StaticContentCreate, StaticContentUpdate, StaticContentRead, StaticContentResponse,
    SupportTicketCreate, SupportTicketRead, SupportTicketStatusUpdate, SupportTicketResponse
)
from app.api.users import get_current_user

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

def render_premium_html(title: str, content: str) -> str:
    # Format linebreaks
    formatted_content = "".join([f"<p>{line}</p>" for line in content.split("\n") if line.strip()])
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Kimbo AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #4F46E5;
            --primary-hover: #4338CA;
            --bg: #0F172A;
            --surface: #1E293B;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --border: #334155;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            line-height: 1.7;
            padding: 2rem 1rem;
            display: flex;
            justify-content: center;
        }}
        
        .container {{
            width: 100%;
            max-width: 800px;
            background-color: var(--surface);
            border: 1px solid var(--border);
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        }}
        
        h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #A5B4FC 0%, #6366F1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .meta {{
            font-size: 0.875rem;
            color: var(--text-muted);
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1rem;
        }}
        
        .content {{
            font-size: 1.05rem;
            font-weight: 400;
            color: #E2E8F0;
        }}
        
        .content p {{
            margin-bottom: 1.5rem;
        }}
        
        .footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta">Last updated: {datetime.utcnow().strftime('%B %d, %Y')}</div>
        <div class="content">
            {formatted_content}
        </div>
        <div class="footer">
            &copy; {datetime.utcnow().year} Kimbo AI. All rights reserved.
        </div>
    </div>
</body>
</html>
"""

# ----------------- STATIC CONTENT ENDPOINTS (Privacy Policy, Terms, etc.) -----------------

@router.get("/static-content/{key}", response_model=StaticContentResponse)
def get_static_content(key: str, session: Session = Depends(get_session)):
    """
    Get static page content by key (e.g. 'privacy_policy', 'terms_conditions').
    """
    statement = select(StaticContent).where(StaticContent.key == key)
    content = session.exec(statement).first()
    if not content:
        raise HTTPException(status_code=404, detail=f"Content for key '{key}' not found.")
    
    return {
        "status": "success",
        "message": f"Content for '{key}' retrieved successfully",
        "data": content
    }

@router.post("/static-content", response_model=StaticContentResponse)
def create_or_update_static_content(
    payload: StaticContentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update static page content (Admin only).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can modify static content.")
    
    statement = select(StaticContent).where(StaticContent.key == payload.key)
    db_content = session.exec(statement).first()
    
    if db_content:
        db_content.title = payload.title
        db_content.content = payload.content
        db_content.updated_at = datetime.utcnow()
    else:
        db_content = StaticContent(
            key=payload.key,
            title=payload.title,
            content=payload.content
        )
        session.add(db_content)
        
    session.commit()
    session.refresh(db_content)
    
    return {
        "status": "success",
        "message": f"Content for '{payload.key}' saved successfully",
        "data": db_content
    }

@router.get("/privacy-policy", response_class=HTMLResponse)
def get_privacy_policy_page(session: Session = Depends(get_session)):
    """
    Render Privacy Policy as a beautiful responsive HTML page.
    """
    statement = select(StaticContent).where(StaticContent.key == "privacy_policy")
    content = session.exec(statement).first()
    title = content.title if content else "Privacy Policy"
    body_content = content.content if content else "Default Privacy Policy. Content will be added shortly."
    return HTMLResponse(content=render_premium_html(title, body_content), status_code=200)

@router.get("/terms-conditions", response_class=HTMLResponse)
def get_terms_conditions_page(session: Session = Depends(get_session)):
    """
    Render Terms and Conditions as a beautiful responsive HTML page.
    """
    statement = select(StaticContent).where(StaticContent.key == "terms_conditions")
    content = session.exec(statement).first()
    title = content.title if content else "Terms and Conditions"
    body_content = content.content if content else "Default Terms and Conditions. Content will be added shortly."
    return HTMLResponse(content=render_premium_html(title, body_content), status_code=200)


# ----------------- SUPPORT TICKETS ENDPOINTS -----------------

@router.post("/support", response_model=SupportTicketResponse)
def submit_support_ticket(
    payload: SupportTicketCreate,
    session: Session = Depends(get_session)
):
    """
    Submit a support/contact inquiry ticket. Anyone (including anonymous guests) can submit.
    """
    db_ticket = SupportTicket.model_validate(payload)
    session.add(db_ticket)
    session.commit()
    session.refresh(db_ticket)
    
    return {
        "status": "success",
        "message": "Support ticket submitted successfully",
        "data": db_ticket
    }

@router.get("/support", response_model=List[SupportTicketRead])
def list_support_tickets(
    status: Optional[SupportStatus] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List support tickets (Admin only). Can filter by status.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view support tickets.")
    
    statement = select(SupportTicket)
    if status:
        statement = statement.where(SupportTicket.status == status)
    
    statement = statement.order_by(SupportTicket.created_at.desc())
    tickets = session.exec(statement).all()
    return tickets

@router.patch("/support/{ticket_id}/status", response_model=SupportTicketResponse)
def update_support_ticket_status(
    ticket_id: int,
    payload: SupportTicketStatusUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update support ticket status (Admin only).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update ticket status.")
    
    db_ticket = session.get(SupportTicket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found.")
    
    db_ticket.status = payload.status
    session.commit()
    session.refresh(db_ticket)
    
    return {
        "status": "success",
        "message": f"Support ticket status updated to {payload.status}",
        "data": db_ticket
    }
