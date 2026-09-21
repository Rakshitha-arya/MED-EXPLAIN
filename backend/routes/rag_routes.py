"""API routes for MedQuAD RAG semantic query search."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.rag_service import query_rag

rag_bp = Blueprint("rag", __name__)


@rag_bp.route("/query", methods=["POST"])
def query_rag_endpoint():
    """Query the MedQuAD FAISS vector store with a medical question."""
    if not request.is_json:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    data = request.get_json() or {}
    query_text = data.get("query")
    if not query_text or not str(query_text).strip():
        return jsonify({"error": "Query string is required and cannot be empty."}), 400

    top_k = data.get("top_k", 3)
    try:
        top_k = int(top_k)
        if top_k < 1:
            return jsonify({"error": "top_k must be at least 1."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "top_k must be an integer."}), 400

    try:
        results = query_rag(query_text=str(query_text).strip(), top_k=top_k)
        return jsonify({
            "query": str(query_text).strip(),
            "results": results,
            "top_k": top_k,
        }), 200
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception:
        return jsonify({"error": "RAG query execution failed. Please try again later."}), 500
