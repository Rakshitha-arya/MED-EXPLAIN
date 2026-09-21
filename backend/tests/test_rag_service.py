"""Tests for rag_service."""
from __future__ import annotations

import pytest

from services.rag_service import query_rag, retrieve_for_report


def test_query_rag_success():
    results = query_rag("blood sugar", top_k=2)
    assert isinstance(results, list)
    assert len(results) == 2
    for record in results:
        assert "question" in record
        assert "answer" in record
        assert "source_row_id" in record
        assert "similarity" in record
        assert isinstance(record["similarity"], float)


def test_query_rag_top_k():
    results_1 = query_rag("glucose", top_k=1)
    results_3 = query_rag("glucose", top_k=3)
    assert len(results_1) == 1
    assert len(results_3) == 3


def test_query_rag_empty_query():
    with pytest.raises(ValueError) as exc_info:
        query_rag("", top_k=3)
    assert "cannot be empty" in str(exc_info.value)

    with pytest.raises(ValueError):
        query_rag("   ", top_k=3)


def test_retrieve_for_report_with_abnormal_params():
    parameters = [
        {
            "test_name": "Hemoglobin",
            "result_value": "11.0",
            "unit": "g/dL",
            "reference_range": "13.5 - 17.5",
            "status": "Low",
        }
    ]
    retrieved = retrieve_for_report(
        extracted_text="Hemoglobin: 11.0 g/dL (13.5 - 17.5)",
        parameters=parameters,
        user_question="Why is my hemoglobin low?",
        top_k=3,
    )
    assert isinstance(retrieved, list)
    assert len(retrieved) <= 3
    if retrieved:
        assert "question" in retrieved[0]
        assert "answer" in retrieved[0]
        assert "similarity" in retrieved[0]


def test_retrieve_for_report_empty_context():
    retrieved = retrieve_for_report(
        extracted_text="", parameters=[], user_question=None, top_k=3
    )
    assert retrieved == []
