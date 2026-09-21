"""Tests for report API routes (upload, analyze, explain, chat, compare, list, trends)."""
from __future__ import annotations

import io
import os
from unittest.mock import patch

import pytest

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # type: ignore

from app import create_app


def create_synthetic_pdf(text_lines: list[str]) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "\n".join(text_lines))
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Route tests must not depend on or write to the runtime report store."""
    monkeypatch.setattr("services.report_ingestion.Config.UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr("services.report_repository.Config.REPORTS_DIR", tmp_path / "reports")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_upload_valid_pdf_report(client):
    lines = [
        "Date: 2026-09-18",
        "Hemoglobin: 14.2 g/dL (13.5 - 17.5)",
        "WBC: 12.0 x10^3/uL (4.5 - 11.0)",
    ]
    pdf_bytes = create_synthetic_pdf(lines)
    data = {"file": (io.BytesIO(pdf_bytes), "sample_report.pdf")}

    response = client.post(
        "/api/reports/upload", data=data, content_type="multipart/form-data"
    )

    assert response.status_code == 200
    json_data = response.get_json()

    assert "report_metadata" in json_data
    assert "extraction_method" in json_data
    assert "extracted_text" in json_data
    assert "parameters" in json_data
    assert "disclaimer" in json_data

    metadata = json_data["report_metadata"]
    assert metadata["file_type"] == "pdf"
    assert metadata["report_date"] == "2026-09-18"

    params = json_data["parameters"]
    assert len(params) >= 2

    hemo = next((p for p in params if "Hemoglobin" in p["test_name"]), None)
    assert hemo is not None
    assert hemo["status"] == "Normal"

    wbc = next((p for p in params if "WBC" in p["test_name"]), None)
    assert wbc is not None
    assert wbc["status"] == "High"

    assert "educational" in json_data["disclaimer"].lower()
    assert "c:" not in metadata["filename"].lower()
    assert "/" not in metadata["filename"] and "\\" not in metadata["filename"]


def test_upload_invalid_file_type(client):
    data = {"file": (io.BytesIO(b"print('hello')"), "script.py")}
    response = client.post(
        "/api/reports/upload", data=data, content_type="multipart/form-data"
    )

    assert response.status_code == 400
    json_data = response.get_json()
    assert "Unsupported file type" in json_data["error"]


def test_upload_missing_file_part(client):
    response = client.post(
        "/api/reports/upload", data={}, content_type="multipart/form-data"
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert "No file part" in json_data["error"]


def test_upload_empty_file(client):
    data = {"file": (io.BytesIO(b""), "empty.pdf")}
    response = client.post(
        "/api/reports/upload", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert "file is empty" in json_data["error"]


def test_upload_oversized_file_is_rejected(client, monkeypatch):
    monkeypatch.setattr("services.report_ingestion.Config.MAX_CONTENT_LENGTH", 10)
    data = {"file": (io.BytesIO(b"%PDF-123456789"), "large.pdf")}
    response = client.post("/api/reports/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "maximum allowed" in response.get_json()["error"]


def test_report_id_path_traversal_is_not_resolved(client):
    response = client.post("/api/reports/../../config.py/chat", json={"question": "test"})
    assert response.status_code in (404, 405)


def test_analyze_report_endpoint(client):
    lines = [
        "Date: 2026-09-18",
        "Fast Glucose: 135 mg/dL (70 - 99)",
    ]
    pdf_bytes = create_synthetic_pdf(lines)
    data = {"file": (io.BytesIO(pdf_bytes), "glucose_report.pdf")}

    response = client.post(
        "/api/reports/analyze", data=data, content_type="multipart/form-data"
    )

    assert response.status_code == 200
    json_data = response.get_json()

    assert "report_metadata" in json_data
    assert "parameters" in json_data
    assert "retrieved_knowledge" in json_data
    assert isinstance(json_data["retrieved_knowledge"], list)
    assert "disclaimer" in json_data

    glucose = next(
        (p for p in json_data["parameters"] if "Glucose" in p["test_name"]), None
    )
    assert glucose is not None
    assert glucose["status"] == "High"


def test_explain_report_endpoint_unconfigured(client):
    lines = ["Date: 2026-09-18", "Hemoglobin: 11.0 g/dL (13.5 - 17.5)"]
    pdf_bytes = create_synthetic_pdf(lines)
    upload_res = client.post(
        "/api/reports/upload",
        data={"file": (io.BytesIO(pdf_bytes), "explain_test.pdf")},
        content_type="multipart/form-data",
    )
    assert upload_res.status_code == 200
    filename = upload_res.get_json()["report_metadata"]["filename"]

    with patch.dict(os.environ, {}, clear=True):
        explain_res = client.post(
            f"/api/reports/{filename}/explain",
            json={"question": "Can you explain my report?"},
        )
        assert explain_res.status_code == 200
        json_data = explain_res.get_json()
        assert json_data["status"] == "not_configured"
        assert "not configured" in json_data["answer"].lower()
        assert "report_context" in json_data
        assert "retrieved_context" in json_data
        assert "disclaimer" in json_data


def test_explain_report_endpoint_configured(client):
    lines = ["Date: 2026-09-18", "Hemoglobin: 11.0 g/dL (13.5 - 17.5)"]
    pdf_bytes = create_synthetic_pdf(lines)
    upload_res = client.post(
        "/api/reports/upload",
        data={"file": (io.BytesIO(pdf_bytes), "explain_test_mock.pdf")},
        content_type="multipart/form-data",
    )
    filename = upload_res.get_json()["report_metadata"]["filename"]

    with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
        explain_res = client.post(
            f"/api/reports/{filename}/explain",
            json={"question": "What does my low hemoglobin mean?"},
        )
        assert explain_res.status_code == 200
        json_data = explain_res.get_json()
        assert json_data["status"] == "success"
        assert "Mocked patient-friendly educational explanation" in json_data["answer"]


def test_chat_with_report_endpoint_configured(client):
    lines = [
        "Date: 2026-09-18",
        "Hemoglobin: 10.5 g/dL (13.5 - 17.5)",
    ]
    pdf_bytes = create_synthetic_pdf(lines)
    upload_res = client.post(
        "/api/reports/upload",
        data={"file": (io.BytesIO(pdf_bytes), "chat_sample.pdf")},
        content_type="multipart/form-data",
    )
    filename = upload_res.get_json()["report_metadata"]["filename"]

    with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
        chat_res = client.post(
            f"/api/reports/{filename}/chat",
            json={"question": "Why is my hemoglobin low?"},
        )

        assert chat_res.status_code == 200
        json_data = chat_res.get_json()

        assert json_data["status"] == "success"
        assert json_data["report_id"] == filename
        assert json_data["question"] == "Why is my hemoglobin low?"
        assert "report_context" in json_data
        assert "retrieved_knowledge" in json_data
        assert json_data["llm_status"] == "configured"
        assert "Mocked patient-friendly educational explanation" in json_data["answer"]
        assert "disclaimer" in json_data


def test_get_reports_list_endpoint(client):
    response = client.get("/api/reports")
    assert response.status_code == 200
    json_data = response.get_json()
    assert "reports" in json_data
    assert "count" in json_data
    assert isinstance(json_data["reports"], list)


def test_compare_reports_endpoint_success(client):
    pdf1 = create_synthetic_pdf(["Date: 2026-01-10", "Hemoglobin: 10.2 g/dL (12-16)"])
    pdf2 = create_synthetic_pdf(["Date: 2026-04-10", "Hemoglobin: 11.5 g/dL (12-16)"])

    up1 = client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf1), "c1.pdf")}, content_type="multipart/form-data")
    up2 = client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf2), "c2.pdf")}, content_type="multipart/form-data")

    fn1 = up1.get_json()["report_metadata"]["filename"]
    fn2 = up2.get_json()["report_metadata"]["filename"]

    cmp_res = client.post("/api/reports/compare", json={"report_ids": [fn1, fn2]})
    assert cmp_res.status_code == 200
    json_data = cmp_res.get_json()

    assert json_data["comparison_metadata"]["report_count"] == 2
    assert "Hemoglobin" in json_data["common_parameters"]
    assert "disclaimer" in json_data


def test_compare_reports_endpoint_validation_errors(client):
    res1 = client.post("/api/reports/compare", json={"report_ids": ["id1"]})
    assert res1.status_code == 400

    res2 = client.post("/api/reports/compare", json={"report_ids": []})
    assert res2.status_code == 400


def test_get_trends_endpoint(client):
    pdf1 = create_synthetic_pdf(["Date: 2026-01-10", "WBC: 6.0 x10^3/uL (4.5-11)"])
    client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf1), "t1.pdf")}, content_type="multipart/form-data")

    res = client.get("/api/reports/trends?parameter=WBC")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["parameter"] == "WBC"
    assert "measurements" in json_data
