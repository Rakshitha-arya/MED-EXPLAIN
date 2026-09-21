"""Sentence Transformer embedding service used by the explicit indexing command."""
from __future__ import annotations

import os
from typing import Sequence

# Keep the Windows indexing process bounded before numerical libraries load.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))
torch.set_num_interop_threads(int(os.getenv("TORCH_NUM_INTEROP_THREADS", "1")))


class EmbeddingService:
    """Loads one pretrained model and produces normalized float32 embeddings."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                device="cpu",
                local_files_only=True,
                model_kwargs={"low_cpu_mem_usage": True},
            )
        return self._model

    def embed(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        if not texts:
            raise ValueError("At least one text is required to create embeddings.")
        embeddings = self.model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(embeddings, dtype=np.float32)
