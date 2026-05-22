"""
scripts/setup_db.py — One-time database initialisation script.

Run this ONCE before starting the backend:
    cd backend
    python scripts/setup_db.py

What it does:
  1. Enables the pgvector extension on Supabase (if not already enabled)
  2. Creates the 'documents' table via SQLAlchemy
  3. Initialises the LangChain pgvector collection tables
  4. Prints a success summary
"""
import sys
import os

# Add backend/ to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from db import engine, Base, check_db_connection
from models.document import Document   # noqa: F401 — import registers model
from config import get_settings

settings = get_settings()


def setup():
    print("\n🔧  ERP Copilot Lite — Database Setup")
    print("=" * 50)

    # 1. Test connection
    print("\n[1/4] Testing database connection...")
    if not check_db_connection():
        print("❌  Cannot connect to database. Check DATABASE_URL in .env")
        sys.exit(1)
    print("    ✅  Connected to Supabase PostgreSQL")

    # 2. Enable pgvector extension
    print("\n[2/4] Enabling pgvector extension...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    print("    ✅  pgvector extension ready")

    # 3. Create SQLAlchemy tables (documents)
    print("\n[3/4] Creating application tables...")
    Base.metadata.create_all(bind=engine)
    print("    ✅  'documents' table created (or already exists)")

    # 4. Init LangChain pgvector tables
    print("\n[4/4] Initialising LangChain pgvector collection...")
    try:
        from services.embedder import get_vector_store
        store = get_vector_store()
        # Calling this triggers LangChain to create langchain_pg_collection
        # and langchain_pg_embedding tables if they don't exist
        print("    ✅  pgvector collection 'erp_chunks' ready")
    except Exception as e:
        print(f"    ⚠️   pgvector collection init warning (may be OK): {e}")

    print("\n" + "=" * 50)
    print("✅  Database setup complete!")
    print("\nNext steps:")
    print("  1. Add your GEMINI_API_KEY to backend/.env")
    print("  2. Run: python scripts/create_dummy_docs.py")
    print("  3. Run: uvicorn main:app --reload")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    setup()
