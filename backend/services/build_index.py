"""Explicit, reproducible MedQuAD FAISS index builder and retrieval smoke test.

Run from the backend directory:
    python -m services.build_index
Or from the project root:
    .venv\\Scripts\\python.exe -m backend.services.build_index
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
from itertools import islice

if __package__ in (None, "", "services"):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from config import Config, PROJECT_ROOT
    from services.embedding_service import EmbeddingService
    from services.medquad_preprocessor import iter_medquad_documents
    from services.vector_store import MedQuADVectorStore
else:
    from backend.config import Config, PROJECT_ROOT
    from backend.services.embedding_service import EmbeddingService
    from backend.services.medquad_preprocessor import iter_medquad_documents
    from backend.services.vector_store import MedQuADVectorStore


def _checkpoint_paths() -> tuple[Path, Path, Path]:
    return (
        Config.FAISS_INDEX_PATH.with_suffix(".faiss.tmp"),
        Config.METADATA_PATH.with_suffix(".jsonl.tmp"),
        Config.CHECKPOINT_PATH,
    )


def _load_checkpoint(
    temporary_index: Path, temporary_metadata: Path, checkpoint_path: Path
) -> tuple[object | None, int, int]:
    paths = (temporary_index, temporary_metadata, checkpoint_path)
    present = [path.is_file() for path in paths]
    if not any(present):
        return None, 0, 0
    if not all(present):
        raise RuntimeError(
            "Incomplete Stage 2 checkpoint: FAISS, metadata, and progress files "
            "must all exist together. Refusing to guess or delete checkpoint files."
        )
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        required = (
            "completed_records", "faiss_vector_count", "metadata_count",
            "next_source_row_id", "embedding_model", "embedding_dimension",
        )
        missing = [field for field in required if field not in checkpoint]
        if missing:
            raise ValueError("missing fields: " + ", ".join(missing))
        import faiss
        index = faiss.read_index(str(temporary_index))
        with temporary_metadata.open(encoding="utf-8") as metadata_file:
            metadata = [json.loads(line) for line in metadata_file if line.strip()]
        metadata_count = len(metadata)
        if index.ntotal != metadata_count:
            raise ValueError(
                f"FAISS count {index.ntotal} does not match metadata count {metadata_count}."
            )
        if checkpoint["completed_records"] != index.ntotal:
            raise ValueError("Checkpoint completed_records does not match FAISS count.")
        if checkpoint["faiss_vector_count"] != index.ntotal:
            raise ValueError("Checkpoint faiss_vector_count does not match FAISS count.")
        if checkpoint["metadata_count"] != metadata_count:
            raise ValueError("Checkpoint metadata_count does not match metadata.")
        if checkpoint["embedding_model"] != Config.EMBEDDING_MODEL_NAME:
            raise ValueError("Checkpoint embedding model does not match configuration.")
        if checkpoint["embedding_dimension"] != index.d:
            raise ValueError("Checkpoint embedding dimension does not match FAISS index.")
        actual_ids = [record["source_row_id"] for record in metadata]
        if actual_ids != list(range(metadata_count)):
            raise ValueError("Checkpoint metadata source_row_id order is invalid.")
        return MedQuADVectorStore(index=index, metadata=metadata), metadata_count, int(
            checkpoint["next_source_row_id"]
        )
    except Exception as exc:
        raise RuntimeError(f"Stage 2 checkpoint is corrupted or invalid: {exc}") from exc


def _write_checkpoint(
    index, completed_records: int, next_source_row_id: int, checkpoint_path: Path
) -> None:
    checkpoint = {
        "completed_records": completed_records,
        "faiss_vector_count": int(index.ntotal),
        "metadata_count": completed_records,
        "next_source_row_id": next_source_row_id,
        "embedding_model": Config.EMBEDDING_MODEL_NAME,
        "embedding_dimension": int(index.d),
    }
    temporary_checkpoint = checkpoint_path.with_suffix(".json.write")
    with temporary_checkpoint.open("w", encoding="utf-8") as file:
        json.dump(checkpoint, file, indent=2)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary_checkpoint, checkpoint_path)


def build_index(max_records: int | None = None, publish: bool = True) -> dict[str, object]:
    """Stream, checkpoint, validate, and atomically publish the MedQuAD index."""
    Config.ensure_runtime_directories()
    expected_record_count = max_records or sum(
        1 for _ in iter_medquad_documents(Config.MEDQUAD_CSV_PATH)
    )
    if max_records is None and expected_record_count != 16407:
        raise ValueError(
            f"Expected 16407 usable MedQuAD records, found {expected_record_count}."
        )

    embedding_service = EmbeddingService(Config.EMBEDDING_MODEL_NAME)
    temporary_index, temporary_metadata, checkpoint_path = _checkpoint_paths()
    temporary_manifest = Config.INDEX_MANIFEST_PATH.with_suffix(".json.tmp")
    store, record_count, next_source_row_id = _load_checkpoint(
        temporary_index, temporary_metadata, checkpoint_path
    )
    if store is None:
        record_count = 0
        next_source_row_id = 0
    temporary_manifest.unlink(missing_ok=True)

    document_iterator = (
        document for document in iter_medquad_documents(Config.MEDQUAD_CSV_PATH)
        if document.source_row_id >= next_source_row_id
    )
    batch_number = 0
    while True:
        batch_limit = Config.EMBEDDING_BATCH_SIZE
        if max_records is not None:
            batch_limit = min(batch_limit, max_records - record_count)
            if batch_limit <= 0:
                break
        batch = list(islice(document_iterator, batch_limit))
        if not batch:
            break
        batch_number += 1
        batch_start = record_count + 1
        batch_end = record_count + len(batch)
        print(f"Embedding batch {batch_number}: records {batch_start}-{batch_end}", flush=True)
        try:
            embeddings = embedding_service.embed(
                [document.retrieval_text for document in batch], Config.EMBEDDING_BATCH_SIZE
            )
        except BaseException:
            print(f"Embedding batch {batch_number} failed for records {batch_start}-{batch_end}.", flush=True)
            traceback.print_exc()
            raise
        print(f"Embedding batch {batch_number} complete: records {batch_start}-{batch_end}", flush=True)
        if store is None:
            store = MedQuADVectorStore.create_empty(embeddings.shape[1])
        if embeddings.shape[0] != len(batch):
            raise ValueError("Embedding count does not match the current document batch.")
        store.add_embeddings(embeddings)
        with temporary_metadata.open("a", encoding="utf-8") as metadata_file:
            for document in batch:
                metadata_file.write(json.dumps({
                    "source_row_id": document.source_row_id,
                    "question": document.question,
                    "answer": document.answer,
                }, ensure_ascii=False) + "\n")
            metadata_file.flush()
            os.fsync(metadata_file.fileno())
        record_count = batch_end
        next_source_row_id = batch[-1].source_row_id + 1
        temporary_index_write = temporary_index.with_suffix(".faiss.write")
        import faiss
        faiss.write_index(store.index, str(temporary_index_write))
        os.replace(temporary_index_write, temporary_index)
        _write_checkpoint(store.index, record_count, next_source_row_id, checkpoint_path)

    if store is None or record_count != expected_record_count:
        raise ValueError(f"Indexed {record_count} records but expected {expected_record_count}.")

    import faiss
    faiss.write_index(store.index, str(temporary_index))
    validated_store = MedQuADVectorStore.load(temporary_index, temporary_metadata)
    if validated_store.index.ntotal != expected_record_count:
        raise ValueError("Temporary FAISS index and metadata failed count validation.")

    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_csv": str(Config.MEDQUAD_CSV_PATH.relative_to(PROJECT_ROOT)),
        "source_sha256": hashlib.sha256(Config.MEDQUAD_CSV_PATH.read_bytes()).hexdigest(),
        "record_count": record_count,
        "embedding_dimension": int(store.index.d),
        "embedding_model": Config.EMBEDDING_MODEL_NAME,
        "index_type": "faiss.IndexFlatIP",
        "normalization": "L2-normalized embeddings; inner product equals cosine similarity",
    }
    with temporary_manifest.open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)
        manifest_file.write("\n")
        manifest_file.flush()
        os.fsync(manifest_file.fileno())

    if not publish:
        return manifest
    os.replace(temporary_index, Config.FAISS_INDEX_PATH)
    os.replace(temporary_metadata, Config.METADATA_PATH)
    os.replace(temporary_manifest, Config.INDEX_MANIFEST_PATH)
    checkpoint_path.unlink(missing_ok=True)
    return manifest


def run_retrieval_smoke_test(top_k: int = 3) -> list[dict[str, object]]:
    """Query a persisted index; this is a verification utility, not an API."""
    store = MedQuADVectorStore.load(Config.FAISS_INDEX_PATH, Config.METADATA_PATH)
    embedding_service = EmbeddingService(Config.EMBEDDING_MODEL_NAME)
    queries = [
        "What is diabetes?",
        "What does high blood sugar mean?",
        "What is hemoglobin A1c?",
    ]
    output: list[dict[str, object]] = []
    for query in queries:
        results = store.search(embedding_service.embed([query]), top_k=top_k)
        output.append({"query": query, "results": results})
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or test the MedQuAD FAISS index.")
    parser.add_argument("--verify-only", action="store_true", help="Skip indexing and run sample searches.")
    parser.add_argument("--top-k", type=int, default=3, help="Results per verification query.")
    parser.add_argument("--max-records", type=int, help="Build only this many records for checkpoint testing.")
    parser.add_argument("--checkpoint-only", action="store_true", help="Keep test artifacts temporary and skip retrieval.")
    args = parser.parse_args()

    if not args.verify_only:
        manifest = build_index(max_records=args.max_records, publish=not args.checkpoint_only)
        print("Built MedQuAD FAISS index:")
        print(json.dumps(manifest, indent=2))
    if not args.checkpoint_only:
        for item in run_retrieval_smoke_test(top_k=args.top_k):
            print(f"\nQuery: {item['query']}")
            for rank, result in enumerate(item["results"], start=1):
                print(f"{rank}. similarity={result['similarity']:.4f}")
                print(f"   question: {result['question']}")
                print(f"   answer: {result['answer'][:500]}")


if __name__ == "__main__":
    main()
