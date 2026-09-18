import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:wifi6@localhost:5432/collabsterdb",
)

engine = create_engine(
    url=DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  
    pool_pre_ping=True, 
)

LocalSession: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():

    db: Session = LocalSession()
    try:
        yield db
    finally:
        db.close()