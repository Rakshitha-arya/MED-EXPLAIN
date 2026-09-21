"""Read-only Stage 8 integrity checks for Python sources and retrieval assets."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import faiss


BACKEND_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    python_files = [
        path for path in BACKEND_DIR.rglob("*.py") if "tmp_pytest" not in path.parts
    ]
    for path in python_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    index = faiss.read_index(str(BACKEND_DIR / "data_store" / "vector_index" / "medquad.faiss"))
    metadata_path = BACKEND_DIR / "data_store" / "vector_index" / "medquad_metadata.jsonl"
    metadata_count = sum(1 for line in metadata_path.open(encoding="utf-8") if line.strip())
    manifest = json.loads(
        (BACKEND_DIR / "data_store" / "vector_index" / "manifest.json").read_text(encoding="utf-8")
    )
    result = {
        "python_files_parsed": len(python_files),
        "faiss_count": index.ntotal,
        "metadata_count": metadata_count,
        "manifest_record_count": manifest["record_count"],
    }
    print(json.dumps(result, indent=2))
    if not (index.ntotal == metadata_count == manifest["record_count"] == 16407):
        raise SystemExit("FAISS and metadata integrity check failed.")


if __name__ == "__main__":
    main()
