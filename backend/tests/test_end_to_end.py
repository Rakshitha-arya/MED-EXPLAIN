"""End-to-end integration test suite covering complete MedExplain workflow requirements A-L."""
from __future__ import annotations

import io
import os
from unittest.mock import patch

import pytest

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # type: ignore

from PIL import Image, ImageDraw
from app import create_app


def create_synthetic_pdf(text_lines: list[str]) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "\n".join(text_lines))
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def create_synthetic_png() -> bytes:
    img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Test Report Image", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("services.report_repository.Config.REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr("services.report_ingestion.Config.UPLOAD_DIR", tmp_path / "uploads")

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_workflow_a_text_pdf_report(client):
    """Workflow A: Text PDF report upload and parsing."""
    pdf_bytes = create_synthetic_pdf(["Date: 2026-09-18", "Hemoglobin: 14.2 g/dL (13.5 - 17.5)"])
    res = client.post(
        "/api/reports/upload",
        data={"file": (io.BytesIO(pdf_bytes), "text_report.pdf")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["extraction_method"] == "pdf_text"
    assert len(json_data["parameters"]) >= 1
    assert json_data["parameters"][0]["status"] == "Normal"


def test_workflow_b_scanned_pdf_report(client):
    """Workflow B: Scanned/image PDF fallback handling."""
    doc = fitz.open()
    doc.new_page()
    scanned_bytes = doc.write()
    doc.close()

    with patch("services.report_ingestion.ocr_extract_from_pdf_bytes") as mock_ocr:
        mock_ocr.return_value = "--- Page 1 ---\nHemoglobin: 12.0 g/dL (13.5 - 17.5)"
        res = client.post(
            "/api/reports/upload",
            data={"file": (io.BytesIO(scanned_bytes), "scanned.pdf")},
            content_type="multipart/form-data",
        )
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["extraction_method"] == "pdf_ocr"
        assert json_data["parameters"][0]["status"] == "Low"


def test_workflow_c_image_report(client):
    """Workflow C: PNG/JPG image report processing."""
    png_bytes = create_synthetic_png()
    with patch("services.report_ingestion.ocr_extract_from_image") as mock_ocr:
        mock_ocr.return_value = "WBC: 12.5 x10^3/uL (4.5 - 11.0)"
        res = client.post(
            "/api/reports/upload",
            data={"file": (io.BytesIO(png_bytes), "lab_scan.png")},
            content_type="multipart/form-data",
        )
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["extraction_method"] == "image_ocr"
        assert json_data["parameters"][0]["status"] == "High"


def test_workflow_d_h_i_multi_reports_compare_trends(client):
    """Workflows D, H, I: Multiple reports upload, compare, and trends retrieval."""
    pdf1 = create_synthetic_pdf(["Date: 2026-01-10", "Hemoglobin: 10.2 g/dL (12-16)"])
    pdf2 = create_synthetic_pdf(["Date: 2026-04-10", "Hemoglobin: 11.5 g/dL (12-16)"])

    r1 = client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf1), "rep1.pdf")}, content_type="multipart/form-data")
    r2 = client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf2), "rep2.pdf")}, content_type="multipart/form-data")

    id1 = r1.get_json()["report_metadata"]["filename"]
    id2 = r2.get_json()["report_metadata"]["filename"]

    # Workflow H: POST /api/reports/compare
    cmp_res = client.post("/api/reports/compare", json={"report_ids": [id1, id2]})
    assert cmp_res.status_code == 200
    cmp_json = cmp_res.get_json()
    assert cmp_json["comparison_metadata"]["report_count"] == 2
    assert "Hemoglobin" in cmp_json["common_parameters"]

    # Workflow I: GET /api/reports/trends
    trends_res = client.get("/api/reports/trends?parameter=Hemoglobin")
    assert trends_res.status_code == 200
    assert trends_res.get_json()["measurement_count"] == 2


def test_workflow_e_rag_query(client):
    """Workflow E: RAG question search API."""
    res = client.post("/api/rag/query", json={"query": "What does high blood sugar mean?", "top_k": 3})
    assert res.status_code == 200
    json_data = res.get_json()
    assert len(json_data["results"]) == 3
    assert "question" in json_data["results"][0]


def test_workflow_f_llm_configured(client):
    """Workflow F: LLM configured using a mocked provider."""
    pdf = create_synthetic_pdf(["Date: 2026-09-18", "Glucose: 140 mg/dL (70 - 99)"])
    up = client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf), "g.pdf")}, content_type="multipart/form-data")
    filename = up.get_json()["report_metadata"]["filename"]

    with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
        res = client.post(f"/api/reports/{filename}/chat", json={"question": "Explain my glucose"})
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["llm_status"] == "configured"
        assert "Mocked" in json_data["answer"]


def test_workflow_g_llm_not_configured(client):
    """Workflow G: LLM not configured state."""
    pdf = create_synthetic_pdf(["Date: 2026-09-18", "Glucose: 140 mg/dL (70 - 99)"])
    up = client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf), "g2.pdf")}, content_type="multipart/form-data")
    filename = up.get_json()["report_metadata"]["filename"]

    with patch.dict(os.environ, {}, clear=True):
        res = client.post(f"/api/reports/{filename}/chat", json={"question": "Explain my glucose"})
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "not_configured"
        assert "not configured" in json_data["answer"].lower()


def test_workflow_j_invalid_file(client):
    """Workflow J: Invalid file rejection."""
    res = client.post("/api/reports/upload", data={"file": (io.BytesIO(b"import os"), "script.py")}, content_type="multipart/form-data")
    assert res.status_code == 400
    assert "Unsupported file type" in res.get_json()["error"]


def test_workflow_k_missing_reference_range(client):
    """Workflow K: Missing reference range => status Unknown."""
    pdf = create_synthetic_pdf(["Date: 2026-09-18", "Hemoglobin: 14.0 g/dL"])
    res = client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf), "norange.pdf")}, content_type="multipart/form-data")
    assert res.status_code == 200
    params = res.get_json()["parameters"]
    assert params[0]["status"] == "Unknown"


def test_workflow_l_qualitative_result(client):
    """Workflow L: Qualitative result => status Unknown."""
    pdf = create_synthetic_pdf(["Date: 2026-09-18", "HBsAg: Positive (Negative)"])
    res = client.post("/api/reports/upload", data={"file": (io.BytesIO(pdf), "qual.pdf")}, content_type="multipart/form-data")
    assert res.status_code == 200
    params = res.get_json()["parameters"]
    assert params[0]["status"] == "Unknown"
