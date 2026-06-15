from fastapi import APIRouter, Depends, HTTPException, Request
from pathlib import Path
from sqlmodel import Session, select
from typing import List, Optional
from app.database import engine, get_session
import uuid
from app.models import PurchaseEntry, User, Product, PurchaseStatus, UserRole
from app.schemas.app_schemas import (
    PurchaseEntryCreate, PurchaseEntryResponse, PurchaseEntryRead,
    PurchaseEntryWithProductRead, PurchaseEntryAdminRead, ProductDetail,
    ContractorDetail, PurchaseEntryWithProductResponse, PurchaseEntryAdminResponse
)
from app.utils.notifications import create_notification
from app.utils.pdf_generator import generate_purchase_pdf
from app.api.users import get_current_admin, get_current_contractor

router = APIRouter()


def get_purchase_pdf_url(purchase_id: int, request: Request) -> Optional[str]:
    invoices_dir = Path("uploads/invoices")
    if not invoices_dir.exists():
        return None

    pattern = f"purchase_{purchase_id}_*.pdf"
    matches = list(invoices_dir.glob(pattern))
    if not matches:
        matches = list(invoices_dir.glob(f"*{purchase_id}*.pdf"))
    if not matches:
        return None

    return f"{str(request.base_url).rstrip('/')}/static/invoices/{matches[0].name}"


# ==============================
# CONTRACTOR APIs
# ==============================
@router.post("/contractor", response_model=PurchaseEntryWithProductResponse)
def add_purchase_contractor(
    purchase_data: PurchaseEntryCreate, 
    session: Session = Depends(get_session),
    contractor_user: User = Depends(get_current_contractor)
):


    # Verify product
    product = session.get(Product, purchase_data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Tokens and Total Amount are calculated based on product details and quantity
    tokens_calculated = int(product.token_points_per_unit * purchase_data.quantity_bought)
    total_calculated = float(product.price_per_unit * purchase_data.quantity_bought)
    
    db_purchase = PurchaseEntry(**purchase_data.dict(), total_amount=total_calculated, contractor_id=contractor_user.id)
    db_purchase.status = PurchaseStatus.PENDING
    db_purchase.tokens_earned = tokens_calculated  # Record but don't give them yet
    
    session.add(db_purchase)
    session.commit()
    session.refresh(db_purchase)

    db_purchase.product = product
    # Notify all admins about the new purchase request
    admin_users = session.exec(select(User).where(User.role == UserRole.ADMIN)).all()
    product_name = product.name if product else f"Product #{purchase_data.product_id}"
    contractor_name = contractor_user.full_name or contractor_user.email
    notification_message = (
        f"New purchase request from {contractor_name}: "
        f"{purchase_data.quantity_bought} x {product_name}."
    )
    for admin in admin_users:
        create_notification(session, admin.id, "New Purchase Request", notification_message)
    session.commit()

    return {
        "status": "success",
        "message": f"Purchase recorded. {tokens_calculated} tokens are pending admin approval.",
        "data": db_purchase
    }

@router.get("/contractor", response_model=List[PurchaseEntryWithProductRead])
def get_purchases_contractor(
    session: Session = Depends(get_session),
    contractor_user: User = Depends(get_current_contractor)
):
    purchases = session.exec(select(PurchaseEntry).where(PurchaseEntry.contractor_id == contractor_user.id).order_by(PurchaseEntry.created_at.desc())).all()
    result = []
    for p in purchases:
        product = session.get(Product, p.product_id)
        product_detail = None
        if product:
            product_detail = ProductDetail(
                id=product.id,
                name=product.name,
                description=product.description,
                unit=product.unit,
                price_per_unit=product.price_per_unit,
                token_points_per_unit=product.token_points_per_unit,
                image_url=product.image_url,
            )
        result.append(PurchaseEntryWithProductRead(
            id=p.id,
            product_id=p.product_id,
            quantity_bought=p.quantity_bought,
            bill_number=p.bill_number,
            contractor_id=p.contractor_id,
            date=p.date,
            status=p.status,
            tokens_earned=p.tokens_earned,
            total_amount=p.total_amount,
            payment_method=p.payment_method,
            transaction_id=p.transaction_id,
            created_at=p.created_at,
            updated_at=p.updated_at,
            product=product_detail,
        ))
    return result

# ==============================
# ADMIN APIs
# ==============================
@router.get("/admin", response_model=List[PurchaseEntryAdminRead])
def get_purchases_admin(
    request: Request,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    purchases = session.exec(select(PurchaseEntry).order_by(PurchaseEntry.created_at.desc())).all()
    result = []
    for p in purchases:
        product = session.get(Product, p.product_id)
        product_detail = None
        if product:
            product_detail = ProductDetail(
                id=product.id,
                name=product.name,
                description=product.description,
                unit=product.unit,
                price_per_unit=product.price_per_unit,
                token_points_per_unit=product.token_points_per_unit,
                image_url=product.image_url,
            )
        contractor = session.get(User, p.contractor_id)
        contractor_detail = None
        if contractor:
            contractor_detail = ContractorDetail(
                id=contractor.id,
                full_name=contractor.full_name,
                mobile_number=contractor.mobile_number,
                contractor_code=contractor.contractor_code,
                address=contractor.address,
            )
        result.append(PurchaseEntryAdminRead(
            id=p.id,
            product_id=p.product_id,
            quantity_bought=p.quantity_bought,
            bill_number=p.bill_number,
            contractor_id=p.contractor_id,
            date=p.date,
            status=p.status,
            tokens_earned=p.tokens_earned,
            total_amount=p.total_amount,
            payment_method=p.payment_method,
            transaction_id=p.transaction_id,
            pdf_url=get_purchase_pdf_url(p.id, request),
            created_at=p.created_at,
            updated_at=p.updated_at,
            product=product_detail,
            contractor=contractor_detail,
        ))
    return result

@router.patch("/admin/{purchase_id}/status", response_model=PurchaseEntryAdminResponse)
def update_purchase_status(
    purchase_id: int,
    status: PurchaseStatus,
    request: Request,
    payment_method: Optional[str] = None,
    upi_id: Optional[str] = None,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    db_purchase = session.get(PurchaseEntry, purchase_id)
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase entry not found")

    if db_purchase.status == PurchaseStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Purchase is already approved.")

    db_purchase.status = status
    # Auto-generate bill number if not set
    if not db_purchase.bill_number:
        db_purchase.bill_number = f"SBBMS-BN-{uuid.uuid4().hex[:8].upper()}"
    
    contractor = session.get(User, db_purchase.contractor_id)
    pdf_url = None

    if status == PurchaseStatus.APPROVED:
        if payment_method:
            db_purchase.payment_method = payment_method
        if upi_id:
            db_purchase.transaction_id = upi_id
            
        # Give tokens to the contractor
        if contractor:
            contractor.total_tokens += db_purchase.tokens_earned
            session.add(contractor)
        create_notification(session, contractor.id, "Purchase Approved", f"Your purchase ID {db_purchase.id} has been approved. Tokens credited.")

        product = session.get(Product, db_purchase.product_id)
        payment_method_str = (payment_method or db_purchase.payment_method or "Cash").upper()
        transaction_id_value = upi_id or db_purchase.transaction_id or ""

        invoice_file = generate_purchase_pdf(
            purchase=db_purchase,
            product=product,
            contractor=contractor,
            payment_method=payment_method_str,
            transaction_id=transaction_id_value,
        )

        pdf_url = f"{str(request.base_url).rstrip('/')}/static/invoices/{invoice_file}"
    else:
        if contractor:
            create_notification(session, contractor.id, "Purchase Status Updated", f"Your purchase ID {db_purchase.id} status changed to {status}.")

    session.add(db_purchase)
    session.commit()
    session.refresh(db_purchase)

    db_purchase.product = session.get(Product, db_purchase.product_id)
    db_purchase.contractor = session.get(User, db_purchase.contractor_id)

    return {
        "status": "success",
        "message": f"Purchase status updated to {status}",
        "data": db_purchase,
        "pdf_url": pdf_url
    }
