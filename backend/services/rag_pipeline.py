"""
services/rag_pipeline.py — LangChain RetrievalQA with Gemini.

Flow:
  1. User question → embed with Gemini gemini-embedding-2 (3072 dims)
  2. Cosine similarity search → top-K chunks from pgvector
  3. Stuff chunks into QA prompt (with citation instructions)
  4. Gemini gemini-2.0-flash generates grounded answer
  5. Return answer + source chunk metadata
"""
from functools import lru_cache
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted
from prompts.qa_prompt import QA_PROMPT
from services.embedder import get_retriever
from config import get_settings
from services.key_manager import key_manager

settings = get_settings()


@lru_cache()
def _get_llm() -> ChatGoogleGenerativeAI:
    """Gemini flash — temperature=0 for factual, grounded QA."""
    return ChatGoogleGenerativeAI(
        model=settings.gemini_chat_model,
        google_api_key=key_manager.get_key(),
        temperature=0,
        convert_system_message_to_human=True,  # Gemini requires this
    )


def build_chain(doc_ids: list[int] = None) -> RetrievalQA:
    """
    Build a RetrievalQA chain scoped to specific documents (or all docs).

    chain_type="stuff": concatenates all retrieved chunks into one prompt.
    return_source_documents=True: returns chunk objects alongside answer.
    """
    llm = _get_llm()
    retriever = get_retriever(doc_ids=doc_ids)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_PROMPT},
    )
    return chain


def ask_question(
    question: str, doc_ids: list[int] = None
) -> dict:
    """
    Run RAG pipeline for a user question.

    Args:
        question: Natural language question
        doc_ids:  Optional list of document IDs to restrict search to

    Returns:
        {
            "answer":  str,
            "sources": [
                {
                    "chunk_id":  str,
                    "filename":  str,
                    "page_num":  int,
                    "source":    str,
                    "text":      str,   # first 300 chars of chunk
                    "score":     None,  # similarity score not available via RetrievalQA
                },
                ...
            ]
        }
    """
    max_attempts = max(len(key_manager.keys), 1) * 2
    last_exception = None

    for attempt in range(max_attempts):
        try:
            chain = build_chain(doc_ids=doc_ids)
            result = chain.invoke({"query": question})
            break
        except (ResourceExhausted, Exception) as e:
            err_msg = str(e).lower()
            is_rate_limit = (
                isinstance(e, ResourceExhausted) or
                "429" in err_msg or
                "quota" in err_msg or
                "resource_exhausted" in err_msg
            )

            if is_rate_limit:
                print(f"[rag_pipeline] Key exhausted/rate-limited. Rotating from index {key_manager.current_index}...")
                key_manager.rotate_key()
                last_exception = e
            else:
                raise RuntimeError(f"RAG pipeline failed: {e}") from e
    else:
        raise RuntimeError(
            f"RAG pipeline failed after exhausting all keys. Last error: {last_exception}"
        ) from last_exception


    answer = result.get("result", "").strip()
    source_docs = result.get("source_documents", [])

    sources = []
    seen_sources = set()

    for doc in source_docs:
        meta = doc.metadata or {}
        source_key = meta.get("source", doc.page_content[:80])

        # Deduplicate sources with same source string
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)

        sources.append(
            {
                "chunk_id":  meta.get("chunk_index", "N/A"),
                "filename":  meta.get("filename", "Unknown"),
                "page_num":  meta.get("page_num", "N/A"),
                "source":    meta.get("source", source_key),
                "text":      doc.page_content[:400],   # preview text
            }
        )

    return {"answer": answer, "sources": sources}
