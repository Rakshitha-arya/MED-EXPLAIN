"""Run the reproducible Stage 8 evaluation against immutable local assets.

Run from ``backend`` with ``python scripts/run_evaluation.py``.  It only reads
the existing FAISS index, MedQuAD metadata, and synthetic test fixtures.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.evaluation import (
    compute_f1,
    compute_precision,
    compute_recall,
    evaluate_ranked_retrieval,
)
from services.ocr_service import is_ocr_available
from services.rag_service import query_rag
from services.report_parser import parse_report_text


FIXTURE_DIR = BACKEND_DIR / "tests" / "fixtures" / "evaluation"


def main() -> None:
    queries = json.loads((FIXTURE_DIR / "synthetic_eval_queries.json").read_text(encoding="utf-8"))
    reports = json.loads((FIXTURE_DIR / "synthetic_eval_reports.json").read_text(encoding="utf-8"))

    ranked = []
    for item in queries:
        hits = query_rag(item["query"], top_k=5)
        ranked.append({
            "retrieved_ids": [hit["source_row_id"] for hit in hits],
            "relevant_ids": item["relevant_source_row_ids"],
        })

    tp = fp = fn = 0
    field_total = field_correct = 0
    for report in reports:
        expected = {p["test_name"].lower(): p for p in report["expected_parameters"]}
        actual = {p["test_name"].lower(): p for p in parse_report_text(report["text"])["parameters"]}
        tp += len(expected.keys() & actual.keys())
        fp += len(actual.keys() - expected.keys())
        fn += len(expected.keys() - actual.keys())
        for name, expected_parameter in expected.items():
            if name in actual:
                for field in ("result_value", "unit", "reference_range", "status"):
                    field_total += 1
                    field_correct += actual[name][field] == expected_parameter[field]

    extraction_precision = compute_precision(tp, fp)
    extraction_recall = compute_recall(tp, fn)
    output = {
        "retrieval": evaluate_ranked_retrieval(ranked),
        "extraction": {
            "precision": extraction_precision,
            "recall": extraction_recall,
            "f1": compute_f1(extraction_precision, extraction_recall),
            "field_accuracy": round(field_correct / field_total, 4) if field_total else 0.0,
            "parameters": tp + fn,
            "field_assertions": field_total,
        },
        "ocr": {"available": is_ocr_available()},
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
