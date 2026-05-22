"""
routers/chat.py — RAG chat endpoint.

POST /api/chat
  Body:  { "question": str, "doc_ids": [int, ...] | null }
  Returns: { "answer": str, "sources": [...], "question": str }
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.rag_pipeline import ask_question

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    doc_ids: list[int] | None = Field(
        default=None,
        description="Optional: restrict search to specific document IDs. null = search all.",
    )


class SourceItem(BaseModel):
    chunk_id: str | int
    filename: str
    page_num: str | int
    source: str
    text: str


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem]
    source_count: int


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Answer a question using RAG over uploaded ERP documents.

    Retrieves top-K chunks via pgvector cosine similarity,
    then generates a grounded answer with Gemini 2.0 Flash.
    Always returns source citations.
    """
    try:
        result = ask_question(
            question=request.question,
            doc_ids=request.doc_ids,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        question=request.question,
        answer=result["answer"],
        sources=result["sources"],
        source_count=len(result["sources"]),
    )
