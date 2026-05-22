"""
services/embedder.py — Manage the pgvector store via LangChain PGVector.

Embedding model : Gemini gemini-embedding-2 (3072 dimensions)
Vector store    : LangChain PGVector → Supabase PostgreSQL
Collection name : "erp_chunks"

LangChain PGVector auto-creates two tables on first use:
  - langchain_pg_collection  (collection metadata)
  - langchain_pg_embedding   (vectors + metadata JSON)

NOTE: langchain-google-genai 1.0.7 uses the v1beta API.
Available embedding models (verified):
  - models/gemini-embedding-2       → 3072 dims  ✅ (our choice)
  - models/gemini-embedding-001     → 768 dims
  - models/gemini-embedding-2-preview → 3072 dims
"""
from functools import lru_cache
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_community.vectorstores.pgvector import DistanceStrategy
from google.api_core.exceptions import ResourceExhausted
from config import get_settings
from services.key_manager import key_manager

settings = get_settings()

COLLECTION_NAME = "erp_chunks"


# ── Embedding model (cached — initialised once) ──────────────
@lru_cache()
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """
    gemini-embedding-2 produces 3072-dimensional vectors.
    task_type="retrieval_document" optimizes embeddings for document storage.
    task_type="retrieval_query" should be used at query time — LangChain
    handles this automatically via embed_query() vs embed_documents().
    """
    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embedding_model,   # models/gemini-embedding-2
        google_api_key=key_manager.get_key(),
        task_type="retrieval_document",          # optimises for indexing
    )


# ── Vector store (cached — one connection per process) ───────
@lru_cache()
def get_vector_store() -> PGVector:
    """
    Returns a PGVector instance connected to Supabase.
    Uses session pooler URL for stable connections.
    """
    embeddings = get_embeddings()
    connection_string = settings.vector_database_url

    return PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=connection_string,
        embedding_function=embeddings,
        distance_strategy=DistanceStrategy.COSINE,
        pre_delete_collection=False,
    )


# ── Public helpers ────────────────────────────────────────────

def add_chunks_to_store(chunks: list[dict]) -> list[str]:
    """
    Embed a list of chunk dicts and store in pgvector.

    Each chunk becomes a LangChain Document with:
      page_content = chunk["text"]
      metadata     = {doc_id, filename, page_num, chunk_index, source}
    """
    max_attempts = max(len(key_manager.keys), 1) * 2
    last_exception = None

    for attempt in range(max_attempts):
        try:
            store = get_vector_store()

            texts = [c["text"] for c in chunks]
            metadatas = [
                {
                    "doc_id":      str(c["doc_id"]),   # store as string for JSON filtering
                    "filename":    c["filename"],
                    "page_num":    c["page_num"],
                    "chunk_index": c["chunk_index"],
                    "source":      c["source"],
                }
                for c in chunks
            ]

            ids = store.add_texts(texts=texts, metadatas=metadatas)
            return ids
        except (ResourceExhausted, Exception) as e:
            err_msg = str(e).lower()
            is_rate_limit = (
                isinstance(e, ResourceExhausted) or
                "429" in err_msg or
                "quota" in err_msg or
                "resource_exhausted" in err_msg
            )
            if is_rate_limit:
                print(f"[embedder] Key exhausted/rate-limited during add_chunks_to_store. Rotating from index {key_manager.current_index}...")
                key_manager.rotate_key()
                last_exception = e
            else:
                raise
    else:
        raise RuntimeError(
            f"add_chunks_to_store failed after exhausting all keys. Last error: {last_exception}"
        ) from last_exception


def similarity_search(query: str, k: int = None, doc_ids: list[int] = None):
    """Semantic similarity search returning (Document, score) tuples."""
    max_attempts = max(len(key_manager.keys), 1) * 2
    last_exception = None

    for attempt in range(max_attempts):
        try:
            store = get_vector_store()
            k = k or settings.top_k_retrieval

            if doc_ids:
                filter_dict = {"doc_id": {"$in": [str(d) for d in doc_ids]}}
                results = store.similarity_search_with_score(
                    query, k=k, filter=filter_dict
                )
            else:
                results = store.similarity_search_with_score(query, k=k)

            return results
        except (ResourceExhausted, Exception) as e:
            err_msg = str(e).lower()
            is_rate_limit = (
                isinstance(e, ResourceExhausted) or
                "429" in err_msg or
                "quota" in err_msg or
                "resource_exhausted" in err_msg
            )
            if is_rate_limit:
                print(f"[embedder] Key exhausted/rate-limited during similarity_search. Rotating from index {key_manager.current_index}...")
                key_manager.rotate_key()
                last_exception = e
            else:
                raise
    else:
        raise RuntimeError(
            f"similarity_search failed after exhausting all keys. Last error: {last_exception}"
        ) from last_exception


def get_retriever(doc_ids: list[int] = None):
    """Return a LangChain retriever for use in RetrievalQA chains."""
    store = get_vector_store()
    search_kwargs = {"k": settings.top_k_retrieval}

    if doc_ids:
        search_kwargs["filter"] = {"doc_id": {"$in": [str(d) for d in doc_ids]}}

    return store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )
