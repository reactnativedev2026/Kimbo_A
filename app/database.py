from sqlmodel import create_engine, SQLModel, Session

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    """Yield a database session for dependency injection."""
    with Session(engine) as session:
        yield session
