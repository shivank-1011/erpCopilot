"""
main.py — FastAPI application entry point.

Mounts all routers, configures CORS for the React frontend,
and provides health check / metadata endpoints.
"""
import sys
import os

# Ensure backend/ is on the Python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from db import check_db_connection
from routers import ingestion, documents, chat, testgen

settings = get_settings()


# ── Lifespan: startup / shutdown logic ───────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 60)
    print("  ERP Copilot Lite — Backend Starting")
    print("=" * 60)

    db_ok = check_db_connection()
    print(f"  Database: {'✅ Connected' if db_ok else '❌ FAILED — check DATABASE_URL in .env'}")

    api_key = settings.gemini_api_key
    if not api_key or api_key == "your_gemini_api_key_here":
        print("  Gemini: ⚠️  API key not set — add GEMINI_API_KEY to backend/.env")
    else:
        print(f"  Gemini: ✅ API key configured ({api_key[:8]}...)")

    print(f"  Environment: {settings.app_env}")
    print(f"  Docs: http://localhost:8000/docs")
    print("=" * 60)

    yield  # Application runs here

    # Shutdown
    print("\n[Shutdown] ERP Copilot Lite backend stopped.")


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="ERP Copilot Lite API",
    description=(
        "RAG-based ERP document assistant. "
        "Upload PDFs/DOCX, ask questions, generate QA test cases."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS — allow React dev server ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mount Routers ─────────────────────────────────────────────
app.include_router(ingestion.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(testgen.router)


# ── Health & Metadata ─────────────────────────────────────────
@app.get("/health", tags=["system"])
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "gemini_configured": bool(
            settings.gemini_api_key
            and settings.gemini_api_key != "your_gemini_api_key_here"
        ),
        "version": "1.0.0",
    }


@app.get("/", tags=["system"])
def root():
    return {
        "app": "ERP Copilot Lite",
        "docs": "/docs",
        "health": "/health",
    }
