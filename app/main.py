import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlmodel import Session 

from app.database import engine, create_db_and_tables
from app.api import images, users, transfers, purchases, schemes, rewards, dashboard, products

app = FastAPI(
    title="Kimbo AI API",
    description="Backend API for Kimbo AI Application",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="uploads"), name="static")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
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
