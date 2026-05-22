"""
services/chunker.py — Split document pages into overlapping chunks.

Uses LangChain's RecursiveCharacterTextSplitter which tries to split
at paragraph → sentence → word boundaries in that preference order.
This preserves semantic units better than a naive character split.
"""
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import get_settings

settings = get_settings()


def build_splitter() -> RecursiveCharacterTextSplitter:
    """
    chunk_size=1000  — ~200–250 words, sweet spot for ERP paragraphs.
    chunk_overlap=200 — 20% overlap prevents losing sentences at boundaries.
    separators: tries paragraph → newline → sentence → word → char.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        length_function=len,
    )


def chunk_pages(
    pages: list[dict],
    doc_id: int,
    filename: str,
) -> list[dict]:
    """
    Split all pages into chunks.

    Args:
        pages:    [{"page_num": int, "text": str}, ...]
        doc_id:   database ID of the parent document
        filename: original filename (used in metadata)

    Returns:
        List of chunk dicts:
        {
            "text":        str,
            "doc_id":      int,
            "filename":    str,
            "page_num":    int,
            "chunk_index": int,   # global index across all pages
            "source":      str,   # human-readable citation string
        }
    """
    splitter = build_splitter()
    chunks = []
    global_idx = 0

    for page in pages:
        page_num = page["page_num"]
        page_text = page["text"].strip()

        if not page_text:
            continue

        texts = splitter.split_text(page_text)

        for local_idx, text in enumerate(texts):
            text = text.strip()
            if len(text) < 30:          # skip tiny orphan chunks
                continue

            chunks.append(
                {
                    "text": text,
                    "doc_id": doc_id,
                    "filename": filename,
                    "page_num": page_num,
                    "chunk_index": global_idx,
                    "source": f"{filename} — Page {page_num} (chunk {local_idx + 1})",
                }
            )
            global_idx += 1

    return chunks
