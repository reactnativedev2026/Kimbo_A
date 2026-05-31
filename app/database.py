import os
from sqlmodel import create_engine, SQLModel, Session

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

database_url = os.getenv("DATABASE_URL", sqlite_url)

# SQLAlchemy 1.4+ deprecated postgres:// prefix in favor of postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# SQLite requires check_same_thread argument, but Postgres/MySQL does not
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    """Yield a database session for dependency injection."""
    with Session(engine) as session:
        yield session
