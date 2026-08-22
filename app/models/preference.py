from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Preference(Base):
    """ORM mapping for the preferences master table."""

    __tablename__ = "preferences"

    preference_id: int = Column(Integer, primary_key=True, nullable=False)
    preference_name: str = Column(String, unique=True, nullable=False)
