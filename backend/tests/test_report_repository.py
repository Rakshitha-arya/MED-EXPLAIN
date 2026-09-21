"""Tests for report_repository service."""
from __future__ import annotations

import pytest

from services.report_repository import (
    delete_report,
    get_multiple_reports,
    get_report,
    list_reports,
    save_report,
)


def test_save_and_get_report(tmp_path, monkeypatch):
    monkeypatch.setattr("services.report_repository.Config.REPORTS_DIR", tmp_path)

    payload = {
        "report_metadata": {
            "filename": "test_report_123.pdf",
            "original_filename": "patient_lab.pdf",
            "file_type": "pdf",
            "page_count": 1,
            "report_date": "2026-01-10",
        },
        "extraction_method": "pdf_text",
        "extracted_text": "Hemoglobin: 10.2 g/dL (12-16)",
        "parameters": [
            {
                "test_name": "Hemoglobin",
                "result_value": "10.2",
                "numeric_value": 10.2,
                "unit": "g/dL",
                "reference_range": "12-16",
                "status": "Low",
            }
        ],
    }

    saved = save_report(payload)
    assert saved["report_id"] == "test_report_123.pdf"
    assert saved["report_date"] == "2026-01-10"

    retrieved = get_report("test_report_123.pdf")
    assert retrieved is not None
    assert retrieved["report_id"] == "test_report_123.pdf"
    assert retrieved["original_filename"] == "patient_lab.pdf"
    assert len(retrieved["parameters"]) == 1


def test_missing_report_date_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr("services.report_repository.Config.REPORTS_DIR", tmp_path)

    payload = {
        "report_metadata": {
            "filename": "nodate_report.pdf",
            "report_date": None,
        },
        "parameters": [],
    }

    saved = save_report(payload)
    assert saved["report_date"] is None


def test_list_and_get_multiple_reports(tmp_path, monkeypatch):
    monkeypatch.setattr("services.report_repository.Config.REPORTS_DIR", tmp_path)

    save_report({"report_metadata": {"filename": "rep1.pdf", "report_date": "2026-01-10"}})
    save_report({"report_metadata": {"filename": "rep2.pdf", "report_date": "2026-04-10"}})

    all_reports = list_reports()
    assert len(all_reports) == 2

    multi = get_multiple_reports(["rep1.pdf", "rep2.pdf"])
    assert len(multi) == 2

    with pytest.raises(ValueError):
        get_multiple_reports(["rep1.pdf", "non_existent.pdf"])


def test_delete_report(tmp_path, monkeypatch):
    monkeypatch.setattr("services.report_repository.Config.REPORTS_DIR", tmp_path)

    save_report({"report_metadata": {"filename": "to_delete.pdf"}})
    assert get_report("to_delete.pdf") is not None

    deleted = delete_report("to_delete.pdf")
    assert deleted is True
    assert get_report("to_delete.pdf") is None


def test_repository_rejects_path_traversal_identifiers(tmp_path, monkeypatch):
    monkeypatch.setattr("services.report_repository.Config.REPORTS_DIR", tmp_path)
    assert get_report("../../config.py") is None
    assert delete_report("..\\..\\config.py") is False
    with pytest.raises(ValueError, match="Invalid report identifier"):
        save_report({"report_metadata": {"filename": "../../outside.pdf"}})
