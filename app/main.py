
from app.api import images
from app.api import users
from app.database import engine
from app.database import create_db_and_tables
from fastapi import FastAPI
from sqlmodel import Session 
from fastapi.staticfiles import StaticFiles
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

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(images.router, prefix="/images", tags=["Images"])
@app.get("/")
def read_root():
    return {"Hello": "Kimbo AI App"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.get("/myProfile/{user_id}")
def read_item(user_id: str):
    return {"user_id": user_id, "name": 'Govind Singh Parihar', "email": 'parmarji74@gmai'}


# import streamlit as st

# st.title("My First Streamlit App")
# st.write("Hello, Streamlit!")

# st.button("Click me")
# st.checkbox("I agree")
# st.radio("Pick one", ["A", "B"])
# st.selectbox("Select one", ["A", "B"])
# st.multiselect("Select multiple", ["A", "B"])
# st.slider("Slide me", 0, 100, 50)
# st.text_input("Enter something")
# st.text_area("Enter a long text")
# st.date_input("Enter a date")
# st.time_input("Enter a time")
# st.file_uploader("Upload a file")
# st.color_picker("Pick a color")
# st.button("Submit")
