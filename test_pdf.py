import os
import uuid
from xhtml2pdf import pisa

date_str = "12-Aug-2023 10:30 AM"
bill_num = "SBBMS-BN-ABCDEF12"
contractor_name = "John Doe"
contractor_mobile = "9876543210"
contractor_code = "CON-1234"
product_name = "Cement Bag"
product_unit = "Bag"
product_price = 350.0
payment_method_str = "ONLINE"
upi_id = "john@ybl"

db_purchase = type('obj', (object,), {'id': 1, 'total_amount': 700.0, 'quantity_bought': 2.0, 'tokens_earned': 10})

upi_row = f"""
<tr>
    <td class="invoice-label">UPI ID / Txn ID</td>
    <td class="invoice-value">{upi_id}</td>
</tr>
"""

bill_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #f8fafc;
    margin: 0;
    padding: 20px;
  }}
  .invoice-card {{
    max-width: 500px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #e2e8f0;
  }}
  .invoice-header {{
    background-color: #059669;
    padding: 24px;
    color: white;
    text-align: center;
  }}
  .invoice-header h1 {{
    margin: 0;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 0.5px;
    color: white;
  }}
  .invoice-header p {{
    margin: 4px 0 0 0;
    font-size: 13px;
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
  }}
  .amount-value {{
    font-size: 32px;
    font-weight: bold;
    color: #059669;
    margin: 6px 0;
  }}
  .badge-paid {{
    background-color: #d1fae5;
    color: #065f46;
    font-size: 11px;
    font-weight: bold;
    padding: 4px 12px;
    text-transform: uppercase;
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
    width: 50%;
  }}
  .invoice-value {{
    color: #0f172a;
    font-weight: bold;
    text-align: right;
    width: 50%;
  }}
  .product-details {{
    background-color: #f1f5f9;
    padding: 16px;
    margin: 18px 0;
    border: 1px solid #e2e8f0;
  }}
  .product-title {{
    font-size: 14px;
    font-weight: bold;
    color: #0f172a;
    margin-bottom: 10px;
    text-transform: uppercase;
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
    font-weight: bold;
    color: #475569;
    margin-bottom: 4px;
  }}
</style>
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
      
      <table class="invoice-table">
        <tr>
          <td class="invoice-label">Payment Mode</td>
          <td class="invoice-value">{payment_method_str}</td>
        </tr>
        {upi_row}
      </table>
    </div>
    <div class="footer">
      <div class="footer-brand">KIMBO BUILD-MART</div>
      <div>Thank you for doing business with us!</div>
    </div>
  </div>
</body>
</html>"""

os.makedirs("uploads", exist_ok=True)
pdf_filename = f"receipt_test_{uuid.uuid4().hex[:6]}.pdf"
pdf_path = os.path.join("uploads", pdf_filename)

try:
    with open(pdf_path, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(bill_html, dest=result_file)
    print("Error status:", pisa_status.err)
except Exception as e:
    import traceback
    traceback.print_exc()
