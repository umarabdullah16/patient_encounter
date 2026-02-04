from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os
from typing import Generator

load_dotenv()

# Prefer an explicit DATABASE_URL env var; otherwise default to a local SQLite DB
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL, echo=False)
    else:
        # Use a file-based SQLite DB by default. Allow multiple threads for tests.
        engine = create_engine(
            "sqlite:///./test.db", connect_args={"check_same_thread": False}, echo=False
        )
    print("Engine Created:", engine.url)
except Exception as e:
    print(e)

SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
