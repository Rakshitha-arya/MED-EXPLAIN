"""FAISS persistence and read-only semantic search for MedQuAD documents."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import faiss
import numpy as np


class MedQuADVectorStore:
    """An inner-product index over normalized Sentence Transformer vectors."""

    def __init__(self, index: faiss.Index, metadata: list[dict[str, Any]]) -> None:
        if index.ntotal != len(metadata):
            raise ValueError("FAISS vector count and metadata count do not match.")
        self.index = index
        self.metadata = metadata

    @classmethod
    def create_empty(cls, dimension: int) -> "MedQuADVectorStore":
        if dimension < 1:
            raise ValueError("Embedding dimension must be positive.")
        # Metadata is intentionally omitted during streamed index construction.
        return cls.__new_empty(dimension)

    @classmethod
    def __new_empty(cls, dimension: int) -> "MedQuADVectorStore":
        instance = object.__new__(cls)
        instance.index = faiss.IndexFlatIP(dimension)
        instance.metadata = []
        return instance

    def add_embeddings(self, embeddings: np.ndarray) -> None:
        if embeddings.ndim != 2 or embeddings.shape[1] != self.index.d:
            raise ValueError("Embedding dimensions do not match this index.")
        self.index.add(np.ascontiguousarray(embeddings, dtype=np.float32))

    @classmethod
    def build(cls, embeddings: np.ndarray, metadata: list[dict[str, Any]]) -> "MedQuADVectorStore":
        if embeddings.ndim != 2 or embeddings.shape[0] == 0:
            raise ValueError("Embeddings must be a non-empty two-dimensional array.")
        if embeddings.shape[0] != len(metadata):
            raise ValueError("Embedding count and metadata count do not match.")
        store = cls.__new_empty(embeddings.shape[1])
        store.add_embeddings(embeddings)
        store.metadata = metadata
        return store

    def save(self, index_path: Path, metadata_path: Path) -> None:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_path))
        with metadata_path.open("w", encoding="utf-8") as file:
            for record in self.metadata:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, index_path: Path, metadata_path: Path) -> "MedQuADVectorStore":
        if not index_path.is_file() or not metadata_path.is_file():
            raise FileNotFoundError(
                "MedQuAD index is unavailable. Run `python -m services.build_index` first."
            )
        with metadata_path.open(encoding="utf-8") as file:
            metadata = [json.loads(line) for line in file if line.strip()]
        return cls(index=faiss.read_index(str(index_path)), metadata=metadata)

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[dict[str, Any]]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        query = np.asarray(query_embedding, dtype=np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)
        if query.ndim != 2 or query.shape[0] != 1:
            raise ValueError("Query embedding must contain exactly one vector.")
        scores, indices = self.index.search(np.ascontiguousarray(query), min(top_k, self.index.ntotal))
        return [
            {"similarity": float(score), **self.metadata[int(position)]}
            for score, position in zip(scores[0], indices[0])
            if position >= 0
        ]
