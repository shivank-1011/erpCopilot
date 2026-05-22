"""
db.py — SQLAlchemy sync engine and session factory.
Uses psycopg2 with Supabase session pooler (port 5432).
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import get_settings

settings = get_settings()

# ── Engine ───────────────────────────────────────────────────
# pool_pre_ping: test connection before use (handles Supabase idle timeouts)
# pool_size / max_overflow: conservative for Supabase free tier
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=(settings.app_env == "development"),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base class for all ORM models ────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency for FastAPI endpoints ────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Health check helper ──────────────────────────────────────
def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return False
