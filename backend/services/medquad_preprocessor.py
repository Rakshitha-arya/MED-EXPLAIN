"""Validation and conservative cleaning for the already-extracted MedQuAD CSV."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import re


REQUIRED_COLUMNS = ("question", "answer")
# Long source answers remain intact in persisted metadata.  Embeddings use a
# bounded excerpt so an unusually long answer cannot dominate indexing time or
# silently exceed the model's token window.
RETRIEVAL_ANSWER_CHAR_LIMIT = 1200


@dataclass(frozen=True)
class MedQuADDocument:
    """A retrieval-ready MedQuAD record preserving its original CSV row number."""

    source_row_id: int
    question: str
    answer: str

    @property
    def retrieval_text(self) -> str:
        return f"Question: {self.question}\nAnswer: {self.answer[:RETRIEVAL_ANSWER_CHAR_LIMIT]}"


def clean_text(value: object) -> str:
    """Normalize whitespace only; do not alter medical wording or claims."""
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def iter_medquad_documents(csv_path: Path):
    """Stream valid records to keep the index build memory-safe."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"MedQuAD CSV was not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        field_names = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in field_names]
        if missing_columns:
            raise ValueError(
                "MedQuAD CSV is missing required column(s): " + ", ".join(missing_columns)
            )
        for source_row_id, row in enumerate(reader):
            question = clean_text(row.get("question"))
            answer = clean_text(row.get("answer"))
            if question and answer:
                yield MedQuADDocument(
                    source_row_id=source_row_id, question=question, answer=answer
                )


def load_medquad_documents(csv_path: Path) -> list[MedQuADDocument]:
    """Load valid question-answer pairs when an in-memory collection is needed."""
    documents = list(iter_medquad_documents(csv_path))
    if not documents:
        raise ValueError("MedQuAD CSV contains no usable question-answer pairs.")
    return documents
