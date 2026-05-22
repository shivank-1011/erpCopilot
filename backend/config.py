"""
config.py — Centralised settings using pydantic-settings.
All values are read from .env automatically.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = ""
    gemini_api_keys: str = ""
    gemini_chat_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "models/text-embedding-004"
    embedding_dimensions: int = 768

    # Database
    database_url: str = ""
    vector_database_url: str = ""

    # RAG settings
    max_chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_retrieval: int = 5
    max_file_size_mb: int = 50
    allowed_extensions: str = "pdf,docx"

    # App
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    @property
    def allowed_ext_list(self) -> list[str]:
        return [e.strip().lower() for e in self.allowed_extensions.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings — reads .env once."""
    return Settings()
