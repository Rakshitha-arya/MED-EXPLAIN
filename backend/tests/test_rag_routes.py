"""Tests for RAG API routes (POST /api/rag/query)."""
from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_query_rag_endpoint_success(client):
    payload = {"query": "What does high blood sugar mean?", "top_k": 3}
    response = client.post("/api/rag/query", json=payload)

    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["query"] == "What does high blood sugar mean?"
    assert json_data["top_k"] == 3
    assert "results" in json_data
    assert isinstance(json_data["results"], list)
    assert len(json_data["results"]) == 3

    first_result = json_data["results"][0]
    assert "question" in first_result
    assert "answer" in first_result
    assert "source_row_id" in first_result
    assert "similarity" in first_result


def test_query_rag_endpoint_missing_query(client):
    response = client.post("/api/rag/query", json={"query": ""})
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Query string is required" in json_data["error"]


def test_query_rag_endpoint_non_json(client):
    response = client.post(
        "/api/rag/query", data="not json", content_type="text/plain"
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Request body must be valid JSON" in json_data["error"]
