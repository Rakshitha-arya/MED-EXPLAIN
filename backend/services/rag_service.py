"""RAG service for retrieving MedQuAD context using SentenceTransformers and FAISS vector index."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from config import Config
from services.embedding_service import EmbeddingService
from services.vector_store import MedQuADVectorStore

# Singleton cache for embedding service and vector store to avoid reloading per request
_embedding_service: Optional[EmbeddingService] = None
_vector_store: Optional[MedQuADVectorStore] = None


def get_embedding_service() -> EmbeddingService:
    """Get or initialize the shared EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(Config.EMBEDDING_MODEL_NAME)
    return _embedding_service


def get_vector_store() -> MedQuADVectorStore:
    """Get or initialize the shared MedQuADVectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = MedQuADVectorStore.load(
            Config.FAISS_INDEX_PATH, Config.METADATA_PATH
        )
    return _vector_store


def query_rag(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Query the MedQuAD FAISS vector store with a text query.

    Returns a list of records containing:
    - question
    - answer
    - source_row_id
    - similarity
    """
    if not query_text or not str(query_text).strip():
        raise ValueError("Query string cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    embedder = get_embedding_service()
    store = get_vector_store()

    query_vec = embedder.embed([query_text.strip()])
    search_results = store.search(query_vec, top_k=top_k)

    formatted_results = []
    for record in search_results:
        formatted_results.append(
            {
                "question": record.get("question", ""),
                "answer": record.get("answer", ""),
                "source_row_id": record.get("source_row_id"),
                "similarity": float(record.get("similarity", 0.0)),
            }
        )

    return formatted_results


def retrieve_for_report(
    extracted_text: str,
    parameters: List[Dict[str, Any]],
    user_question: Optional[str] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Perform report-aware retrieval.

    Combines user question or abnormal lab findings into targeted MedQuAD vector searches.
    Retrieved knowledge is returned clearly demarcated from report contents.
    """
    search_queries: List[str] = []

    # 1. User question takes primary query focus if present
    if user_question and user_question.strip():
        search_queries.append(user_question.strip())

    # 2. Extract abnormal lab parameters (High / Low / Unknown) for targeted context retrieval
    abnormal_params = [
        p
        for p in parameters
        if p.get("status") in ("High", "Low") and p.get("test_name")
    ]
    for param in abnormal_params:
        test_name = param["test_name"]
        status = param["status"]
        search_queries.append(f"What causes {status.lower()} {test_name}?")

    # 3. If no user question or abnormal params, fallback to general medical terms or full report snippet
    if not search_queries:
        if parameters:
            first_test = parameters[0].get("test_name", "")
            if first_test:
                search_queries.append(f"What is {first_test} test?")
        elif extracted_text and extracted_text.strip():
            # Use snippet of report text
            snippet = " ".join(extracted_text.split()[:20])
            search_queries.append(snippet)

    if not search_queries:
        return []

    results_by_id: Dict[Any, Dict[str, Any]] = {}
    for query_str in search_queries:
        try:
            hits = query_rag(query_str, top_k=top_k)
            for hit in hits:
                row_id = hit.get("source_row_id")
                if row_id not in results_by_id:
                    results_by_id[row_id] = hit
                else:
                    # Keep highest similarity score
                    if hit["similarity"] > results_by_id[row_id]["similarity"]:
                        results_by_id[row_id] = hit
        except ValueError:
            continue

    # Sort combined hits by similarity descending and cap at top_k
    sorted_hits = sorted(
        results_by_id.values(), key=lambda x: x["similarity"], reverse=True
    )
    return sorted_hits[:top_k]
