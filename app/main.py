import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlmodel import Session 

from app.database import engine, create_db_and_tables
from app.migrations import run_migrations
from app.api import images, users, transfers, purchases, schemes, rewards, dashboard, products, common, notifications

app = FastAPI(
    title="Kimbo AI API",
    description="Backend API for Kimbo AI Application",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="uploads"), name="static")

def seed_static_content():
    from sqlmodel import Session, select
    from app.models import StaticContent
    
    defaults = {
        "privacy_policy": {
            "title": "Privacy Policy",
            "content": "This is the default Privacy Policy for Kimbo AI. Please modify this in the admin panel."
        },
        "terms_conditions": {
            "title": "Terms and Conditions",
            "content": "This is the default Terms and Conditions for Kimbo AI. Please modify this in the admin panel."
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

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    run_migrations()
    seed_static_content()
    
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
