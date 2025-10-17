from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

TESTING = os.getenv("TESTING") == "1"

if TESTING:
    SQLALCHEMY_DATABASE_URL = "sqlite+pysqlite:///:memory:"
else:
    import os as _os
    DB_PATH = _os.path.join(_os.path.dirname(__file__), "app.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite+pysqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool if TESTING else None,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
