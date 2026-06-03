from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta
from collections import defaultdict
from app.database import engine
from app.models import User, UserRole, MaterialTransfer, PurchaseEntry, PurchaseStatus, Scheme, RewardRedeem, Product
from app.schemas.app_schemas import AdminDashboardStats, ContractorDashboardStats, EarningChartItem, RecentPurchaseItem
from app.api.users import get_current_user

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.get("/admin", response_model=AdminDashboardStats)
def get_admin_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    total_contractors = len(session.exec(select(User).where(User.role == UserRole.CONTRACTOR)).all())
    total_approved_purchases = len(session.exec(
        select(PurchaseEntry).where(PurchaseEntry.status == PurchaseStatus.APPROVED)
    ).all())
    total_redeemed = len(session.exec(select(RewardRedeem)).all())
    active_schemes = len(session.exec(select(Scheme).where(Scheme.is_active == True)).all())

    # Fetch all approved purchases for chart data
    approved_purchases = session.exec(
        select(PurchaseEntry).where(PurchaseEntry.status == PurchaseStatus.APPROVED)
    ).all()

    now = datetime.utcnow()

    # --- Daily earnings (last 7 days) ---
    daily_map = defaultdict(float)
    for i in range(7):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_map[day] = 0.0
    for p in approved_purchases:
        day_key = p.date.strftime("%Y-%m-%d")
        if day_key in daily_map:
            daily_map[day_key] += p.total_amount
    daily_earnings = [
        EarningChartItem(label=k, amount=v)
        for k, v in sorted(daily_map.items())
    ]

    # --- Weekly earnings (last 4 weeks) ---
    weekly_map = defaultdict(float)
    for i in range(4):
        week_start = now - timedelta(weeks=i, days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        week_label = f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b')}"
        weekly_map[week_label] = 0.0
        for p in approved_purchases:
            if week_start <= p.date <= week_end:
                weekly_map[week_label] += p.total_amount
    weekly_earnings = [
        EarningChartItem(label=k, amount=v)
        for k, v in weekly_map.items()
    ]

    # --- Monthly earnings (last 6 months) ---
    monthly_map = defaultdict(float)
    for i in range(6):
        month_date = now.replace(day=1) - timedelta(days=i * 30)
        month_label = month_date.strftime("%b %Y")
        monthly_map[month_label] = 0.0
    for p in approved_purchases:
        m_label = p.date.strftime("%b %Y")
        if m_label in monthly_map:
            monthly_map[m_label] += p.total_amount
    monthly_earnings = [
        EarningChartItem(label=k, amount=v)
        for k, v in monthly_map.items()
    ]

    # --- Recent 5 purchase requests ---
    from sqlalchemy import desc
    recent_purchases_db = session.exec(
        select(PurchaseEntry).order_by(desc(PurchaseEntry.date)).limit(5)
    ).all()
    recent_purchases = []
    for p in recent_purchases_db:
        contractor = session.get(User, p.contractor_id)
        product = session.get(Product, p.product_id)
        recent_purchases.append(RecentPurchaseItem(
            id=p.id,
            contractor_name=contractor.full_name if contractor else "Unknown",
            product_name=product.name if product else f"Product #{p.product_id}",
            quantity_bought=p.quantity_bought,
            total_amount=p.total_amount,
            tokens_earned=p.tokens_earned,
            status=p.status.value,
            bill_number=p.bill_number,
            date=p.date,
        ))

    return {
        "total_contractors": total_contractors,
        "total_approved_purchases": total_approved_purchases,
        "total_redeemed_rewards": total_redeemed,
        "active_schemes": active_schemes,
        "daily_earnings": daily_earnings,
        "weekly_earnings": weekly_earnings,
        "monthly_earnings": monthly_earnings,
        "recent_purchases": recent_purchases,
    }

@router.get("/contractor", response_model=ContractorDashboardStats)
def get_contractor_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CONTRACTOR:
        raise HTTPException(status_code=403, detail="Contractor access required")

    total_purchases = len(session.exec(select(PurchaseEntry).where(PurchaseEntry.contractor_id == current_user.id)).all())
    pending_redeems = len(session.exec(select(RewardRedeem).where(
        RewardRedeem.contractor_id == current_user.id,
        RewardRedeem.status == "pending"
    )).all())

    return {
        "total_tokens": current_user.total_tokens,
        "total_purchases": total_purchases,
        "pending_redeems": pending_redeems
    }
