"""
models/document.py — SQLAlchemy ORM model for uploaded documents.
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_type = Column(String(10), nullable=False)  # 'pdf' or 'docx'
    chunk_count = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="processing")  # processing | ready | error

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.original_filename,
            "file_type": self.file_type,
            "chunk_count": self.chunk_count,
            "page_count": self.page_count,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
