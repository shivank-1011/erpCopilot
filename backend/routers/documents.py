"""
routers/documents.py — Document listing and chunk retrieval endpoints.

GET  /api/documents               — List all uploaded documents
GET  /api/documents/{id}          — Single document metadata
DELETE /api/documents/{id}        — Delete a document
GET  /api/documents/{id}/chunks   — Get chunks for a document (for test gen)
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import get_db
from models.document import Document

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """List all documents ordered by upload time (newest first)."""
    docs = (
        db.query(Document)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return {"documents": [d.to_dict() for d in docs]}


@router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Get metadata for a specific document."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    return doc.to_dict()


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Delete a document and its chunks from both PostgreSQL and pgvector.
    pgvector rows are deleted by filtering cmetadata->>'doc_id'.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")

    # Delete from langchain_pg_embedding (pgvector table)
    try:
        db.execute(
            text(
                """
                DELETE FROM langchain_pg_embedding
                WHERE cmetadata->>'doc_id' = :doc_id
                """
            ),
            {"doc_id": str(doc_id)},
        )
    except Exception as e:
        print(f"[Delete] Could not remove pgvector rows for doc {doc_id}: {e}")

    db.delete(doc)
    db.commit()

    return {"status": "deleted", "doc_id": doc_id, "filename": doc.original_filename}


@router.get("/documents/{doc_id}/chunks")
def get_document_chunks(
    doc_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Retrieve text chunks for a specific document.
    Used by the frontend Test Case Generator to let the user select a section.

    Queries langchain_pg_embedding directly using JSON metadata filter.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")

    if doc.status != "ready":
        return {
            "doc_id": doc_id,
            "status": doc.status,
            "chunks": [],
            "message": "Document is still being processed. Please wait.",
        }

    try:
        rows = db.execute(
            text(
                """
                SELECT
                    lpe.uuid,
                    lpe.document AS text,
                    lpe.cmetadata->>'page_num'    AS page_num,
                    lpe.cmetadata->>'chunk_index' AS chunk_index,
                    lpe.cmetadata->>'source'      AS source
                FROM langchain_pg_embedding lpe
                JOIN langchain_pg_collection lpc ON lpe.collection_id = lpc.uuid
                WHERE lpc.name = 'erp_chunks'
                  AND lpe.cmetadata->>'doc_id' = :doc_id
                ORDER BY (lpe.cmetadata->>'chunk_index')::int
                LIMIT :limit
                """
            ),
            {"doc_id": str(doc_id), "limit": limit},
        ).fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chunks: {e}",
        )

    chunks = [
        {
            "uuid":        str(row.uuid),
            "text":        row.text,
            "page_num":    row.page_num,
            "chunk_index": row.chunk_index,
            "source":      row.source,
            "preview":     (row.text[:150] + "...") if len(row.text) > 150 else row.text,
        }
        for row in rows
    ]

    return {"doc_id": doc_id, "filename": doc.original_filename, "chunks": chunks}
