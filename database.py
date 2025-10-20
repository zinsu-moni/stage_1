from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user_4cd78551:b97a7c1ca9507cc93bdb9f409f32d12d@db.pxxl.pro:22344/db_1da15fcc")


if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Stringsanalysis(Base):

    __tablename__ = "string_analysis"
    
    id = Column(String, primary_key=True, index=True)  
    value = Column(String, nullable=False, unique=True, index=True)
    length = Column(Integer, nullable=False)
    is_palindrome = Column(Boolean, nullable=False, index=True)
    unique_characters = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=False, index=True)
    word_hash = Column(String, nullable=False)
    character_frequency_map = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

def drop_db():
    Base.metadata.drop_all(bind=engine)