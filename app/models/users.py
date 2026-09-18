

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

PROFILE_VISIBILITY_PUBLIC:  str = "public"
PROFILE_VISIBILITY_PRIVATE: str = "private"


class Users(Base):
    __tablename__ = "users"

    user_id            = Column(Integer, primary_key=True)
    profile_visibility = Column(String(30), nullable=False, default=PROFILE_VISIBILITY_PUBLIC)