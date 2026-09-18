from sqlalchemy import Column, Integer, String, JSON, Float, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True)
    likes = Column(Integer)
    comments = Column(Integer)
    shares = Column(Integer)
    saves = Column(Integer)
    watch_time = Column(Integer)
    tags = Column(JSON)
    friends = Column(Integer)
    communities = Column(JSON)
    spam_probability = Column(Float)
    creator_reputation = Column(Float)
    report_count = Column(Integer)
    is_duplicate = Column(Boolean)

    creator_id = Column(Integer, nullable=True)

    content_type = Column(String, nullable=True)