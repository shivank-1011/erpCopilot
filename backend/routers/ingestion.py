"""
routers/ingestion.py — Document upload endpoint.

POST /api/upload
  - Accepts PDF or DOCX file
  - Detects duplicates via SHA-256 hash
  - Parses → chunks → embeds → stores in pgvector
  - Saves document metadata to PostgreSQL
"""
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from db import get_db
from models.document import Document
from services.parser import parse_document, compute_file_hash
from services.chunker import chunk_pages
from services.embedder import add_chunks_to_store
from config import get_settings

router = APIRouter(prefix="/api", tags=["ingestion"])
settings = get_settings()


def _process_and_embed(doc_id: int, chunks: list[dict], db_url: str):
    """
    Background task: embed chunks and update document status.
    Runs after the HTTP response is returned so the upload feels fast.
    """
    from db import SessionLocal
    db = SessionLocal()
    try:
        # Embed and store in pgvector
        add_chunks_to_store(chunks)

        # Update document status to "ready"
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = "ready"
            db.commit()
    except Exception as e:
        db = SessionLocal()
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = "error"
            db.commit()
        print(f"[Embedding] Failed for doc_id={doc_id}: {e}")
    finally:
        db.close()


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest a PDF or DOCX file.

    Returns immediately with document metadata.
    Embedding runs as a background task.
    """
    # ── Validate file type ───────────────────────────────────
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in settings.allowed_ext_list:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(settings.allowed_ext_list)}",
        )

    # ── Read file bytes ──────────────────────────────────────
    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb} MB.",
        )

    # ── Duplicate detection ──────────────────────────────────
    file_hash = compute_file_hash(file_bytes)
    existing = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing:
        return {
            "status": "duplicate",
            "message": f"Document '{existing.original_filename}' was already uploaded.",
            "document": existing.to_dict(),
        }

    # ── Parse document ───────────────────────────────────────
    try:
        pages, page_count, file_type = parse_document(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # ── Chunk text ───────────────────────────────────────────
    # We need a temp doc_id for chunking metadata; use -1 as placeholder
    # and update after DB insert
    doc = Document(
        filename=file_hash[:12] + f".{ext}",
        original_filename=file.filename,
        file_hash=file_hash,
        file_size_bytes=len(file_bytes),
        file_type=file_type,
        page_count=page_count,
        chunk_count=0,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Now chunk with the real doc_id
    chunks = chunk_pages(pages, doc_id=doc.id, filename=file.filename)
    doc.chunk_count = len(chunks)
    db.commit()

    # ── Schedule embedding as background task ────────────────
    background_tasks.add_task(_process_and_embed, doc.id, chunks, settings.database_url)

    return {
        "status": "processing",
        "message": f"Document '{file.filename}' uploaded. Embedding {len(chunks)} chunks in background.",
        "document": doc.to_dict(),
    }
