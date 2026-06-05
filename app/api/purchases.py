from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from app.database import engine, get_session
import uuid
from app.models import PurchaseEntry, User, Product, PurchaseStatus
from app.schemas.app_schemas import PurchaseEntryCreate, PurchaseEntryResponse, PurchaseEntryRead, PurchaseEntryWithProductRead, ProductDetail
from app.api.users import get_current_admin, get_current_contractor

router = APIRouter()

# ==============================
# CONTRACTOR APIs
# ==============================
@router.post("/contractor", response_model=PurchaseEntryResponse)
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
    purchases = session.exec(select(PurchaseEntry).where(PurchaseEntry.contractor_id == contractor_user.id)).all()
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
@router.get("/admin", response_model=List[PurchaseEntryRead])
def get_purchases_admin(
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    purchases = session.exec(select(PurchaseEntry)).all()
    return purchases

@router.patch("/admin/{purchase_id}/status", response_model=PurchaseEntryResponse)
def update_purchase_status(
    purchase_id: int,
    status: PurchaseStatus,
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
    
    # Notify the contractor about status change
    from app.utils.notifications import create_notification
    contractor = session.get(User, db_purchase.contractor_id)
    
    bill_html = None
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
        
        # Fetch product and build Khatabook-style HTML bill
        product = session.get(Product, db_purchase.product_id)
        
        contractor_name = contractor.full_name if contractor else "Unknown Contractor"
        contractor_mobile = contractor.mobile_number if contractor else "N/A"
        contractor_code = contractor.contractor_code if contractor else "N/A"
        
        product_name = product.name if product else f"Product ID {db_purchase.product_id}"
        product_price = product.price_per_unit if product else 0.0
        product_unit = product.unit if product else "Piece"
        
        date_str = db_purchase.date.strftime('%d-%b-%Y %I:%M %p')
        bill_num = db_purchase.bill_number or "N/A"
        
        payment_method_str = (payment_method or "Cash").upper()
        
        upi_row = ""
        if payment_method_str == "ONLINE" and upi_id:
            upi_row = f"""
            <table class="invoice-table" style="margin-bottom: 0;">
              <tr>
                <td class="invoice-label">UPI ID / Txn ID</td>
                <td class="invoice-value">{{upi_id}}</td>
              </tr>
            </table>
            """
            
        bill_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: 'Inter', Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #f8fafc;
    margin: 0;
    padding: 20px;
  }}
  .invoice-card {{
    max-width: 500px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    border: 1px solid #e2e8f0;
  }}
  .invoice-header {{
    background-color: #059669;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    padding: 24px;
    color: white;
    text-align: center;
  }}
  .invoice-header h1 {{
    margin: 0;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: white;
  }}
  .invoice-header p {{
    margin: 4px 0 0 0;
    font-size: 13px;
    opacity: 0.9;
    color: white;
  }}
  .invoice-body {{
    padding: 24px;
  }}
  .amount-section {{
    text-align: center;
    padding: 16px 0;
  }}
  .amount-label {{
    font-size: 12px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
  }}
  .amount-value {{
    font-size: 32px;
    font-weight: 800;
    color: #059669;
    margin: 6px 0;
  }}
  .badge-paid {{
    display: inline-block;
    background-color: #d1fae5;
    color: #065f46;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .divider {{
    border-top: 1px dashed #cbd5e1;
    margin: 20px 0;
  }}
  .invoice-table {{
    width: 100%;
    margin-bottom: 12px;
  }}
  .invoice-table td {{
    font-size: 13.5px;
  }}
  .invoice-label {{
    color: #64748b;
    font-weight: 500;
    width: 50%;
  }}
  .invoice-value {{
    color: #0f172a;
    font-weight: 600;
    text-align: right;
    width: 50%;
  }}
  .product-details {{
    background-color: #f1f5f9;
    border-radius: 10px;
    padding: 16px;
    margin: 18px 0;
    border: 1px solid #e2e8f0;
  }}
  .product-title {{
    font-size: 14px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .footer {{
    text-align: center;
    padding: 20px;
    background-color: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-size: 12px;
    color: #64748b;
  }}
  .footer-brand {{
    font-weight: 800;
    color: #475569;
    margin-bottom: 4px;
    letter-spacing: 0.5px;
  }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
  <div class="invoice-card">
    <div class="invoice-header">
      <h1>KIMBO BUILD-MART</h1>
      <p>Payment Receipt & Token Summary</p>
    </div>
    <div class="invoice-body">
      <div class="amount-section">
        <div class="amount-label">Payment Amount</div>
        <div class="amount-value">₹{db_purchase.total_amount:.2f}</div>
        <div class="badge-paid">Receipt Generated</div>
      </div>
      
      <div class="divider"></div>
      
      <table class="invoice-table">
        <tr>
          <td class="invoice-label">Receipt/Purchase ID</td>
          <td class="invoice-value">#KB-PUR-{db_purchase.id}</td>
        </tr>
        <tr>
          <td class="invoice-label">Date & Time</td>
          <td class="invoice-value">{date_str}</td>
        </tr>
        <tr>
          <td class="invoice-label">Bill Number</td>
          <td class="invoice-value">{bill_num}</td>
        </tr>
      </table>
      
      <div class="divider"></div>
      
      <table class="invoice-table">
        <tr>
          <td class="invoice-label">Contractor Name</td>
          <td class="invoice-value">{contractor_name}</td>
        </tr>
        <tr>
          <td class="invoice-label">Mobile Number</td>
          <td class="invoice-value">{contractor_mobile}</td>
        </tr>
        <tr>
          <td class="invoice-label">Contractor Code</td>
          <td class="invoice-value">{contractor_code}</td>
        </tr>
      </table>
      
      <div class="product-details">
        <div class="product-title">Itemized Purchase</div>
        <table class="invoice-table">
          <tr>
            <td class="invoice-label">{product_name}</td>
            <td class="invoice-value">{db_purchase.quantity_bought} {product_unit} @ ₹{product_price:.2f}/{product_unit}</td>
          </tr>
          <tr>
            <td class="invoice-label">Reward Points Earned</td>
            <td class="invoice-value" style="color: #059669;">+{db_purchase.tokens_earned} Points</td>
          </tr>
        </table>
      </div>
      
      <table class="invoice-table" style="margin-bottom: 0;">
        <tr>
          <td class="invoice-label">Payment Mode</td>
          <td class="invoice-value">{payment_method_str}</td>
        </tr>
      </table>
      {upi_row}
    </div>
    <div class="footer">
      <div class="footer-brand">KIMBO BUILD-MART</div>
      <div>Thank you for doing business with us!</div>
    </div>
  </div>
</body>
</html>"""

        import os
        from xhtml2pdf import pisa
        
        os.makedirs("uploads", exist_ok=True)
        pdf_filename = f"receipt_{db_purchase.id}_{uuid.uuid4().hex[:6]}.pdf"
        pdf_path = os.path.join("uploads", pdf_filename)
        
        pdf_html = bill_html.replace('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">', '')
        with open(pdf_path, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(pdf_html, dest=result_file)
            
        if not pisa_status.err:
            pdf_url = f"/static/{pdf_filename}"

    else:
        if contractor:
            create_notification(session, contractor.id, "Purchase Status Updated", f"Your purchase ID {db_purchase.id} status changed to {status}.")

    session.add(db_purchase)
    session.commit()
    session.refresh(db_purchase)

    return {
        "status": "success",
        "message": f"Purchase status updated to {status}",
        "data": db_purchase,
        "bill_html": bill_html,
        "pdf_url": pdf_url
    }
