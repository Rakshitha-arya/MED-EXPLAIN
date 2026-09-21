"""Tests for evaluation metrics and evaluation benchmark execution."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from services.evaluation import (
    compute_cer,
    compute_f1,
    compute_mrr,
    compute_precision,
    compute_precision_at_k,
    compute_recall,
    compute_recall_at_k,
    compute_wer,
    evaluate_ranked_retrieval,
)
from services.llm_service import generate_response, prepare_prompt
from services.rag_service import query_rag
from services.report_parser import parse_report_text

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "evaluation"


def test_metric_functions_basic():
    # CER & WER
    assert compute_cer("hello", "hello") == 0.0
    assert compute_wer("hello world", "hello world") == 0.0
    assert compute_cer("abc", "abd") > 0.0

    # Precision, Recall, F1
    assert compute_precision(8, 2) == 0.8
    assert compute_recall(8, 2) == 0.8
    assert compute_f1(0.8, 0.8) == 0.8

    # Edge cases
    assert compute_precision(0, 0) == 0.0
    assert compute_recall(0, 0) == 0.0
    assert compute_f1(0.0, 0.0) == 0.0

    # Recall@K and Precision@K
    retrieved = [1, 2, 3, 4, 5]
    gt_set = {2, 9}
    assert compute_recall_at_k(retrieved, gt_set, k=1) == 0.0
    assert compute_recall_at_k(retrieved, gt_set, k=3) == 1.0
    assert compute_precision_at_k(retrieved, gt_set, k=3) == 0.3333

    # MRR
    retrieved_lists = [[10, 20, 30], [5, 15, 25]]
    gt_sets = [{20}, {5}]
    # First query match at rank 2 (1/2 = 0.5), second match at rank 1 (1/1 = 1.0) -> MRR = (0.5 + 1.0)/2 = 0.75
    assert compute_mrr(retrieved_lists, gt_sets) == 0.75


def test_faiss_retrieval_benchmark():
    queries_file = FIXTURE_DIR / "synthetic_eval_queries.json"
    assert queries_file.is_file()

    with queries_file.open(encoding="utf-8") as f:
        eval_queries = json.load(f)

    evaluations = []

    for item in eval_queries:
        query_text = item["query"]
        relevant_ids = item["relevant_source_row_ids"]

        hits = query_rag(query_text, top_k=5)
        hit_ids = [h.get("source_row_id") for h in hits]

        evaluations.append({"retrieved_ids": hit_ids, "relevant_ids": relevant_ids})

    metrics = evaluate_ranked_retrieval(evaluations)
    assert set(metrics) == {
        "recall_at_1", "precision_at_1", "recall_at_3", "precision_at_3",
        "recall_at_5", "precision_at_5", "mrr",
    }
    assert all(0.0 <= value <= 1.0 for value in metrics.values())


def test_extraction_benchmark():
    reports_file = FIXTURE_DIR / "synthetic_eval_reports.json"
    assert reports_file.is_file()

    with reports_file.open(encoding="utf-8") as f:
        eval_reports = json.load(f)

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for rep in eval_reports:
        text = rep["text"]
        expected = rep["expected_parameters"]

        parsed = parse_report_text(text)
        extracted = parsed["parameters"]

        expected_by_name = {
            parameter["test_name"].lower(): parameter
            for parameter in expected
        }
        extracted_by_name = {
            parameter["test_name"].lower(): parameter
            for parameter in extracted
        }
        for name, expected_parameter in expected_by_name.items():
            assert name in extracted_by_name
            actual_parameter = extracted_by_name[name]
            for field in ("result_value", "unit", "reference_range", "status"):
                assert actual_parameter[field] == expected_parameter[field]

        # Match extracted vs expected parameters by name
        extracted_names = {p["test_name"].strip().lower() for p in extracted}
        expected_names = {p["test_name"].strip().lower() for p in expected}

        tp = len(extracted_names & expected_names)
        fp = len(extracted_names - expected_names)
        fn = len(expected_names - extracted_names)

        total_tp += tp
        total_fp += fp
        total_fn += fn

    precision = compute_precision(total_tp, total_fp)
    recall = compute_recall(total_tp, total_fn)
    f1 = compute_f1(precision, recall)

    assert precision >= 0.8
    assert recall >= 0.8
    assert f1 >= 0.8


def test_generation_grounding_eval():
    report_context = {
        "report_metadata": {"report_date": "2026-09-18"},
        "extracted_text": "Hemoglobin: 10.2 g/dL (12-16)",
        "parameters": [
            {
                "test_name": "Hemoglobin",
                "result_value": "10.2",
                "unit": "g/dL",
                "reference_range": "12-16",
                "status": "Low",
            }
        ],
    }

    retrieved_context = [
        {
            "source_row_id": 100,
            "question": "What is anemia?",
            "answer": "Anemia is a condition with low hemoglobin...",
            "similarity": 0.89,
        }
    ]

    with patch.dict("os.environ", {"LLM_PROVIDER": "mock"}):
        resp = generate_response(
            report_context, retrieved_context, "Why is my hemoglobin 10.2?"
        )
        assert resp["status"] == "success"
        prepared_prompt = resp["prepared_prompt"]

        sys_inst = prepared_prompt["system_instruction"]
        usr_prompt = prepared_prompt["user_prompt"]

        # Grounding checks
        assert "DO NOT diagnose" in sys_inst
        assert "DO NOT recommend" in sys_inst
        assert "disclaimer" in sys_inst.lower()

        assert "Hemoglobin" in usr_prompt
        assert "10.2" in usr_prompt
        assert "12-16" in usr_prompt
        assert "What is anemia?" in usr_prompt

        # The mock provider's fixed educational response introduces neither a
        # patient value/range nor diagnosis/treatment language. The API layer
        # attaches its separate patient-facing disclaimer.
        answer = resp["answer"].lower()
        assert "10.2" not in answer and "12-16" not in answer
        assert "diagnos" not in answer
        assert "treatment" not in answer and "medication" not in answer
