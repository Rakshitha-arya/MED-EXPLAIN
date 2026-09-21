"""Application configuration and project-safe paths."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"


class Config:
    """Configuration shared by the Flask app and indexing utilities."""

    load_dotenv(BACKEND_DIR / ".env")

    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    DATA_DIR = DATA_DIR
    MEDQUAD_CSV_PATH = DATA_DIR / "processed_medquad.csv"
    DATA_STORE_DIR = BACKEND_DIR / "data_store"
    UPLOAD_DIR = DATA_STORE_DIR / "uploads"
    REPORTS_DIR = DATA_STORE_DIR / "reports"
    VECTOR_INDEX_DIR = DATA_STORE_DIR / "vector_index"
    FAISS_INDEX_PATH = VECTOR_INDEX_DIR / "medquad.faiss"
    METADATA_PATH = VECTOR_INDEX_DIR / "medquad_metadata.jsonl"
    INDEX_MANIFEST_PATH = VECTOR_INDEX_DIR / "manifest.json"
    CHECKPOINT_PATH = VECTOR_INDEX_DIR / "medquad_checkpoint.json.tmp"

    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

    @classmethod
    def ensure_runtime_directories(cls) -> None:
        """Create runtime storage folders without processing any user data."""
        for directory in (cls.UPLOAD_DIR, cls.REPORTS_DIR, cls.VECTOR_INDEX_DIR):
            directory.mkdir(parents=True, exist_ok=True)
