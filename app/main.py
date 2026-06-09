import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlmodel import Session 

from app.database import engine, create_db_and_tables
from app.migrations import run_migrations
from app.api import images, users, transfers, purchases, schemes, rewards, dashboard, products, common, notifications

app = FastAPI(
    title="SBBMS API",
    description="Backend API for SBBMS - Shri Balaj Building Material and Supplier",
    version="1.0.0"
)
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

def seed_static_content():
    from sqlmodel import Session, select
    from app.models import StaticContent
    
    defaults = {
        "privacy_policy": {
            "title": "Privacy Policy",
            "content": (
                "Welcome to SBBMS (Shri Balaj Building Material and Supplier). "
                "We respect your privacy and are committed to protecting your personal information. "
                "This policy describes how we collect, use, and safeguard your data when you use our services.\n\n"
                "Information Collected: We may collect personal data such as name, email, phone number, shipping address, and billing details. "
                "We also collect order history and communication preferences to improve our service.\n\n"
                "Use of Information: Your data is used to process orders, provide support, improve products, and send important notifications related to your account. "
                "We do not sell your personal information to third parties.\n\n"
                "Security: We take reasonable steps to protect your data from unauthorized access, disclosure, or alteration. "
                "However, no system is completely secure, and we encourage you to keep your account details safe.\n\n"
                "Data Sharing: SBBMS may share information with service providers, logistics partners, or legal authorities when required. "
                "This is only done to support order fulfillment, fraud prevention, or compliance with the law.\n\n"
                "Your Rights: You can request access to your personal information, request corrections, or ask for account deletion. "
                "Please contact our support team for any privacy-related requests."
            )
        },
        "terms_conditions": {
            "title": "Terms and Conditions",
            "content": (
                "Welcome to SBBMS (Shri Balaj Building Material and Supplier). "
                "By using our website or services, you agree to be bound by these terms and conditions.\n\n"
                "Order Acceptance: Orders are subject to acceptance by SBBMS. We reserve the right to decline or cancel any order at our discretion.\n\n"
                "Pricing and Payment: All product prices are displayed in Indian Rupees. Payment must be completed at checkout using approved payment methods.\n\n"
                "Delivery: Delivery timelines are estimates and may vary based on location and logistics availability. SBBMS is not responsible for delays caused by third-party delivery services.\n\n"
                "Returns and Refunds: Returns are handled based on our return policy. Approved returns will be processed after inspection, and refunds will be issued accordingly.\n\n"
                "Account Responsibility: Users are responsible for keeping their account details secure and for all activity that occurs under their account.\n\n"
                "Liability: SBBMS is not liable for indirect or consequential damages resulting from use of our services. Our liability is limited to the amount paid for the relevant order.\n\n"
                "Changes to Terms: We may modify these terms at any time. Continued use of the platform constitutes acceptance of any revised terms."
            )
        },
        "delete_account": {
            "title": "Delete Account",
            "content": (
                "At SBBMS (Shri Balaj Building Material and Supplier), we respect your choice to close your account. "
                "This page explains what happens when you delete your account.\n\n"
                "Account Closure: Requesting account deletion will deactivate your access to SBBMS services and remove your ability to place new orders.\n\n"
                "Data Retention: Certain records may be retained for legal, tax, or business purposes, even after account deletion.\n\n"
                "Pending Orders: Please ensure any active or pending orders are resolved before deleting your account.\n\n"
                "Notifications: You will stop receiving order updates, newsletters, and promotional messages after your account is deleted.\n\n"
                "Support Contact: If you need assistance with deleting your account, contact our support team for guidance and confirmation."
            )
        }
    }
    
    with Session(engine) as session:
        for key, info in defaults.items():
            statement = select(StaticContent).where(StaticContent.key == key)
            db_content = session.exec(statement).first()
            if not db_content:
                db_content = StaticContent(
                    key=key,
                    title=info["title"],
                    content=info["content"]
                )
                session.add(db_content)
        session.commit()

def init_firebase():
    import firebase_admin
    from firebase_admin import credentials
    
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "app/firebase-credentials.json")
    if not os.path.isabs(cred_path):
        if not os.path.exists(cred_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            resolved_path = os.path.join(project_root, cred_path)
            if os.path.exists(resolved_path):
                cred_path = resolved_path

    if os.path.exists(cred_path):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print(f"[FIREBASE] Initialized successfully using: {cred_path}")
        except Exception as e:
            print(f"[FIREBASE] Error initializing Firebase: {e}")
    else:
        print(f"[FIREBASE] Credentials file not found at: {cred_path}. Push notifications will not work.")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    run_migrations()
    seed_static_content()
    init_firebase()
    
def get_session():
    with Session(engine) as session:
        yield session

# Include Routers
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(images.router, prefix="/images", tags=["Images"])
app.include_router(transfers.router, prefix="/transfers", tags=["Material Transfers"])
app.include_router(purchases.router, prefix="/purchases", tags=["Purchases"])
app.include_router(schemes.router, prefix="/schemes", tags=["Schemes"])
app.include_router(rewards.router, prefix="/rewards", tags=["Rewards"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(common.router, prefix="/common", tags=["Common"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

@app.get("/", response_class=HTMLResponse, tags=["Main"])
def read_root():
    # Get path to index.html
    html_file_path = os.path.join(os.path.dirname(__file__), "index.html")
    
    # Read and return the HTML file
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>HTML file not found! Please create app/index.html</h1>", status_code=404)
