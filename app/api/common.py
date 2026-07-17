from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from app.database import engine, get_session
from app.models import StaticContent, SupportTicket, User, UserRole, SupportStatus, FAQ
from app.schemas.common_schema import (
    StaticContentCreate, StaticContentUpdate, StaticContentRead, StaticContentResponse,
    SupportTicketCreate, SupportTicketRead, SupportTicketStatusUpdate, SupportTicketResponse,
    FAQCreate, FAQUpdate, FAQRead, FAQResponse, FAQListResponse
)
from app.api.users import get_current_user

router = APIRouter()

def render_premium_html(title: str, content: str) -> str:
    # Format linebreaks and preserve paragraph spacing
    formatted_content = "".join([f"<p>{line}</p>" for line in content.split("\n") if line.strip()])
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - SBBMS</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2F855A;
            --secondary: #F6E05E;
            --bg: #F8FAFC;
            --surface: #FFFFFF;
            --text-main: #0F172A;
            --text-muted: #4A5568;
            --border: #E2E8F0;
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
            line-height: 1.8;
            padding: 2rem 1rem;
            display: flex;
            justify-content: center;
        }}
        
        .container {{
            width: 100%;
            max-width: 900px;
            background-color: var(--surface);
            border: 1px solid var(--border);
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
        }}
        
        .brand {{
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        
        .brand-mark {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #2F855A 0%, #38B2AC 100%);
            border-radius: 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 1rem;
        }}
        
        h1 {{
            font-size: 2.4rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }}
        
        .subtitle {{
            font-size: 1rem;
            color: var(--text-muted);
            margin-bottom: 1.75rem;
        }}
        
        .meta {{
            font-size: 0.95rem;
            color: var(--text-muted);
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1rem;
        }}
        
        .content {{
            font-size: 1.05rem;
            font-weight: 400;
            color: var(--text-main);
        }}
        
        .content p {{
            margin-bottom: 1.4rem;
        }}
        
        .content ul {{
            margin-left: 1.2rem;
            margin-bottom: 1.4rem;
            color: var(--text-main);
        }}
        
        .content li {{
            margin-bottom: 0.75rem;
        }}
        
        .footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.9rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="brand">
            <div class="brand-mark">S</div>
            <div>
                <div style="font-size:1.1rem;font-weight:700;">SBBMS</div>
                <div style="font-size:0.95rem;color:var(--text-muted);">Shri Balaj Building Material and Supplier</div>
            </div>
        </div>
        <h1>{title}</h1>
        <div class="subtitle">Your trusted construction supplies partner.</div>
        <div class="meta">Last updated: {datetime.utcnow().strftime('%B %d, %Y')}</div>
        <div class="content">
            {formatted_content}
        </div>
        <div class="footer">
            &copy; {datetime.utcnow().year} SBBMS. Shri Balaj Building Material and Supplier. All rights reserved.
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
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)
    html_file_path = os.path.join(app_dir, "privacy_policy.html")
    
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
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
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)
    html_file_path = os.path.join(app_dir, "terms_conditions.html")
    
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        statement = select(StaticContent).where(StaticContent.key == "terms_conditions")
        content = session.exec(statement).first()
        title = content.title if content else "Terms and Conditions"
        body_content = content.content if content else (
            "Welcome to SBBMS (Shri Balaj Building Material and Supplier). "
            "By using our services, you agree to the following terms and conditions. "
            "Please read these terms carefully before placing any orders or using our platform.\n\n"
            "1. Order Acceptance: Orders are subject to acceptance by SBBMS. We reserve the right to refuse or cancel any order for any reason, including pricing errors or product availability.\n\n"
            "2. Pricing and Payments: All prices are shown in Indian Rupees. Payment must be completed at checkout. We accept the payment methods displayed on our platform.\n\n"
            "3. Delivery and Shipping: Delivery timelines are estimates and may vary based on stock availability and location. SBBMS is not responsible for delays caused by third-party logistics partners.\n\n"
            "4. Returns and Refunds: Returns are handled according to our return policy and may require prior approval. Refunds will be issued once the returned items are inspected.\n\n"
            "5. User Responsibilities: Users must provide accurate information and keep their account details secure. Any misuse of the platform may result in account suspension.\n\n"
            "6. Intellectual Property: All content, graphics, logos, and materials on the platform are the property of SBBMS and may not be used without permission.\n\n"
            "7. Limitation of Liability: SBBMS is not liable for indirect, incidental, or consequential damages arising from the use of our services.\n\n"
            "8. Changes to Terms: We may update these terms at any time. Users will be notified of material changes, and continued use of the service constitutes acceptance of the revised terms."
        )
        return HTMLResponse(content=render_premium_html(title, body_content), status_code=200)

@router.get("/delete-account", response_class=HTMLResponse)
def get_delete_account_page(session: Session = Depends(get_session)):
    """
    Render Delete Account interactive request page as a beautiful responsive HTML page.
    """
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)
    html_file_path = os.path.join(app_dir, "delete_account.html")
    
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        statement = select(StaticContent).where(StaticContent.key == "delete_account")
        content = session.exec(statement).first()
        title = content.title if content else "Delete Account"
        body_content = content.content if content else (
            "At SBBMS (Shri Balaj Building Material and Supplier), we respect your decision to close your account. "
            "Please review the following information before proceeding.\n\n"
            "1. Account Closure: When you request account deletion, your access to the SBBMS platform will be removed.\n\n"
            "2. Data Retention: Certain information may be retained for legal, tax, or security reasons in accordance with our data retention policy.\n\n"
            "3. Outstanding Orders: Any pending or active orders should be completed or canceled prior to requesting deletion.\n\n"
            "4. Notifications: You will no longer receive order updates, promotional messages, or other notifications after the account is closed.\n\n"
            "5. Contact Support: If you need help with deleting your account, please contact our support team through the support page.\n\n"
            "To proceed with account deletion, log in to your account and follow the provided delete account workflow in the app."
        )
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

    # Send push notification to user if registered
    if db_ticket.user_id:
        from app.utils.notifications import create_notification
        create_notification(
            session,
            db_ticket.user_id,
            "Support Ticket Updated",
            f"Your support ticket #{db_ticket.id} status has been updated to {payload.status}.",
            notification_type="support_ticket",
            related_id=db_ticket.id
        )
        session.commit()
    
    return {
        "status": "success",
        "message": f"Support ticket status updated to {payload.status}",
        "data": db_ticket
    }

# ----------------- FAQ ENDPOINTS -----------------

@router.post("/faqs", response_model=FAQResponse, tags=["FAQs"])
def create_faq(
    payload: FAQCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new FAQ (Admin only).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create FAQs.")
        
    db_faq = FAQ.model_validate(payload)
    session.add(db_faq)
    session.commit()
    session.refresh(db_faq)
    return {
        "status": "success",
        "message": "FAQ created successfully",
        "data": db_faq
    }

@router.get("/faqs", response_model=FAQListResponse, tags=["FAQs"])
def get_faqs(
    active_only: bool = True,
    session: Session = Depends(get_session)
):
    """
    Get all FAQs (Public). By default, returns only active FAQs.
    """
    statement = select(FAQ)
    if active_only:
        statement = statement.where(FAQ.is_active == True)
    
    statement = statement.order_by(FAQ.created_at.desc())
    faqs = session.exec(statement).all()
    return {
        "status": "success",
        "message": "FAQs retrieved successfully",
        "data": faqs
    }

@router.get("/faqs/{faq_id}", response_model=FAQResponse, tags=["FAQs"])
def get_faq(
    faq_id: int,
    session: Session = Depends(get_session)
):
    """
    Get a single FAQ by ID (Public).
    """
    db_faq = session.get(FAQ, faq_id)
    if not db_faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return {
        "status": "success",
        "message": "FAQ retrieved successfully",
        "data": db_faq
    }

@router.patch("/faqs/{faq_id}", response_model=FAQResponse, tags=["FAQs"])
def update_faq(
    faq_id: int,
    payload: FAQUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update an FAQ (Admin only).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update FAQs.")
        
    db_faq = session.get(FAQ, faq_id)
    if not db_faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_faq, key, value)
        
    session.add(db_faq)
    session.commit()
    session.refresh(db_faq)
    return {
        "status": "success",
        "message": "FAQ updated successfully",
        "data": db_faq
    }

@router.delete("/faqs/{faq_id}", tags=["FAQs"])
def delete_faq(
    faq_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an FAQ (Admin only).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete FAQs.")
        
    db_faq = session.get(FAQ, faq_id)
    if not db_faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
        
    session.delete(db_faq)
    session.commit()
    return {
        "status": "success",
        "message": "FAQ deleted successfully",
        "deleted_id": faq_id
    }

@router.post("/admin/backup-db", tags=["Admin"])
def backup_database(
    current_user: User = Depends(get_current_user)
):
    """
    Trigger manual database backup and upload it to Cloudinary (Admin only).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can backup the database.")
        
    from app.utils.backup import run_backup
    result = run_backup()
    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result
