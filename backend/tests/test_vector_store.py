import numpy as np

from services.vector_store import MedQuADVectorStore


def test_faiss_store_round_trip_and_search(tmp_path):
    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    metadata = [
        {"source_row_id": 10, "question": "alpha", "answer": "first"},
        {"source_row_id": 11, "question": "beta", "answer": "second"},
    ]
    store = MedQuADVectorStore.build(embeddings, metadata)
    index_path = tmp_path / "test.faiss"
    metadata_path = tmp_path / "test.jsonl"
    store.save(index_path, metadata_path)

    loaded_store = MedQuADVectorStore.load(index_path, metadata_path)
    results = loaded_store.search(np.array([1.0, 0.0], dtype=np.float32), top_k=1)
    assert loaded_store.index.ntotal == 2
    assert results[0]["source_row_id"] == 10
    assert results[0]["similarity"] == 1.0
