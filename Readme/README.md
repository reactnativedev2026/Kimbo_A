# KimboA — Changes Log (3rd June 2026)

---

## 1. Auto-Generate Bill Number on Purchase Approval

**File:** `app/api/purchases.py`

- When admin approves a purchase via `PATCH /purchases/admin/{purchase_id}/status`, a **bill number is now auto-generated** by the backend if not already set.
- Format: `SBBMS-BN-XXXXXXXX` (8-char uppercase hex from UUID)

```python
# Example generated bill number
"SBBMS-BN-1A2B3C4D"
```

---

## 2. Product Details in Contractor Purchases Response

**Files:** `app/api/purchases.py`, `app/schemas/app_schemas.py`

- `GET /purchases/contractor` now returns **full product details** nested inside each purchase item.
- New schemas added:
  - `ProductDetail` — `id`, `name`, `description`, `unit`, `price_per_unit`, `token_points_per_unit`, `image_url`
  - `PurchaseEntryWithProductRead` — extends `PurchaseEntryRead` with a `product` field

### Response Example

```json
{
  "id": 1,
  "product_id": 5,
  "quantity_bought": 10,
  "total_amount": 5000.0,
  "status": "pending",
  "product": {
    "id": 5,
    "name": "Cement",
    "description": "UltraTech Cement",
    "unit": "Bag",
    "price_per_unit": 500.0,
    "token_points_per_unit": 10.0,
    "image_url": "https://..."
  }
}
```

---

## 3. Admin Dashboard Enhancements

**Files:** `app/api/dashboard.py`, `app/schemas/app_schemas.py`

### 3.1 Replaced `total_material_transfers` → `total_approved_purchases`

- Now counts only **approved** purchases instead of material transfers.

### 3.2 Earning Chart Data (Daily / Weekly / Monthly)

New fields added to `GET /dashboard/admin` response for chart rendering:

| Field              | Description                        |
|--------------------|------------------------------------|
| `daily_earnings`   | Last **7 days** — label: `YYYY-MM-DD`, amount: ₹ total |
| `weekly_earnings`  | Last **4 weeks** — label: `DD Mon - DD Mon`, amount: ₹ total |
| `monthly_earnings` | Last **6 months** — label: `Mon YYYY`, amount: ₹ total |

Each item has:
```json
{ "label": "2026-06-03", "amount": 15000.0 }
```

### 3.3 Recent 5 Purchase Requests

- Added `recent_purchases` array with the **latest 5 purchase requests** (any status).
- Each item includes `contractor_name` and `product_name`.

New schema: `RecentPurchaseItem`
- `id`, `contractor_name`, `product_name`, `quantity_bought`, `total_amount`, `tokens_earned`, `status`, `bill_number`, `date`

### Full Admin Dashboard Response Example

```json
{
  "total_contractors": 5,
  "total_approved_purchases": 12,
  "total_redeemed_rewards": 3,
  "active_schemes": 2,
  "daily_earnings": [
    { "label": "2026-05-28", "amount": 15000.0 },
    { "label": "2026-05-29", "amount": 8500.0 }
  ],
  "weekly_earnings": [
    { "label": "02 Jun - 08 Jun", "amount": 45000.0 }
  ],
  "monthly_earnings": [
    { "label": "Jun 2026", "amount": 120000.0 }
  ],
  "recent_purchases": [
    {
      "id": 25,
      "contractor_name": "Rajesh Kumar",
      "product_name": "Cement",
      "quantity_bought": 10.0,
      "total_amount": 5000.0,
      "tokens_earned": 100,
      "status": "pending",
      "bill_number": "SBBMS-BN-A1B2C3D4",
      "date": "2026-06-03T12:00:00"
    }
  ]
}
```

---

## Files Modified

| File | Changes |
|------|---------|
| `app/api/purchases.py` | Bill number auto-gen + product details in contractor response |
| `app/api/dashboard.py` | Approved purchases count, earning charts, recent 5 purchases |
| `app/schemas/app_schemas.py` | New schemas: `ProductDetail`, `PurchaseEntryWithProductRead`, `EarningChartItem`, `RecentPurchaseItem`, updated `AdminDashboardStats` |

---

## 4. Reward Redemption Integrated with Schemes

**Files:** `app/models.py`, `app/schemas/app_schemas.py`, `app/api/rewards.py`

- The `RewardRedeem` model is now connected to `Scheme`.
- Added `tokens_required` to the `Scheme` model to dynamically cost redemptions.
- The `POST /rewards/redeem` endpoint now accepts `scheme_id` instead of a manual description and token count.
- Automatically handles token verification and deduction for a more user-friendly flow.

---

## 5. Global DB Session Bug Fix

**Files:** `app/api/rewards.py`, `app/api/dashboard.py`, `app/api/transfers.py`, `app/api/schemes.py`, `app/api/purchases.py`, `app/api/products.py`, `app/api/notifications.py`, `app/api/common.py`

- **Bug:** Attempting to process data using `current_user` caused a 500 Internal Server Error (`InvalidRequestError: Object is already attached to session 'X' (this is 'Y')`).
- **Cause:** Duplicate definitions of `get_session()` in multiple API routers caused FastAPI's Dependency Injection to instantiate multiple separate database sessions per HTTP request.
- **Fix:** Removed all local `get_session()` instances inside router files. They now correctly import `get_session` centrally from `app.database`, ensuring a single session lifecycle per request.
