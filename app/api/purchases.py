from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from app.database import engine
from app.models import PurchaseEntry, User, Product, PurchaseStatus
from app.schemas.app_schemas import PurchaseEntryCreate, PurchaseEntryResponse, PurchaseEntryRead
from app.api.users import get_current_admin, get_current_contractor

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

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

@router.get("/contractor", response_model=List[PurchaseEntryRead])
def get_purchases_contractor(
    session: Session = Depends(get_session),
    contractor_user: User = Depends(get_current_contractor)
):
    purchases = session.exec(select(PurchaseEntry).where(PurchaseEntry.contractor_id == contractor_user.id)).all()
    return purchases

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
    
    # Notify the contractor about status change
    from app.utils.notifications import create_notification
    contractor = session.get(User, db_purchase.contractor_id)
    
    bill_html = None
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
            <div class="invoice-row">
              <span class="invoice-label">UPI ID / Txn ID</span>
              <span class="invoice-value">{upi_id}</span>
            </div>
            """
            
        bill_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: 'Inter', sans-serif;
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
  }}
  .invoice-header p {{
    margin: 4px 0 0 0;
    font-size: 13px;
    opacity: 0.9;
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
  .invoice-row {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
    font-size: 13.5px;
  }}
  .invoice-label {{
    color: #64748b;
    font-weight: 500;
  }}
  .invoice-value {{
    color: #0f172a;
    font-weight: 600;
    text-align: right;
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
      
      <div class="invoice-row">
        <span class="invoice-label">Receipt/Purchase ID</span>
        <span class="invoice-value">#KB-PUR-{db_purchase.id}</span>
      </div>
      <div class="invoice-row">
        <span class="invoice-label">Date & Time</span>
        <span class="invoice-value">{date_str}</span>
      </div>
      <div class="invoice-row">
        <span class="invoice-label">Bill Number</span>
        <span class="invoice-value">{bill_num}</span>
      </div>
      
      <div class="divider"></div>
      
      <div class="invoice-row">
        <span class="invoice-label">Contractor Name</span>
        <span class="invoice-value">{contractor_name}</span>
      </div>
      <div class="invoice-row">
        <span class="invoice-label">Mobile Number</span>
        <span class="invoice-value">{contractor_mobile}</span>
      </div>
      <div class="invoice-row">
        <span class="invoice-label">Contractor Code</span>
        <span class="invoice-value">{contractor_code}</span>
      </div>
      
      <div class="product-details">
        <div class="product-title">Itemized Purchase</div>
        <div class="invoice-row">
          <span class="invoice-label">{product_name}</span>
          <span class="invoice-value">{db_purchase.quantity_bought} {product_unit} @ ₹{product_price:.2f}/{product_unit}</span>
        </div>
        <div class="invoice-row" style="margin-bottom: 0;">
          <span class="invoice-label">Reward Points Earned</span>
          <span class="invoice-value" style="color: #059669;">+{db_purchase.tokens_earned} Points</span>
        </div>
      </div>
      
      <div class="invoice-row">
        <span class="invoice-label">Payment Mode</span>
        <span class="invoice-value">{payment_method_str}</span>
      </div>
      {upi_row}
    </div>
    <div class="footer">
      <div class="footer-brand">KIMBO BUILD-MART</div>
      <div>Thank you for doing business with us!</div>
    </div>
  </div>
</body>
</html>"""

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
        "bill_html": bill_html
    }
