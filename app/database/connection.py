from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, 
    # check_same_thread=False is only for SQLite
    connect_args=(
        {"check_same_thread": False} 
        if "sqlite" in settings.DATABASE_URL 
        else {"client_encoding": "utf8"}
    ),
    # Added pool settings for PostgreSQL
    pool_pre_ping=True if "postgresql" in settings.DATABASE_URL else False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
