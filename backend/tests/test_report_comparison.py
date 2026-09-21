"""Tests for report_comparison service."""
from __future__ import annotations

import pytest

from services.report_comparison import compare_reports
from services.report_repository import save_report


@pytest.fixture(autouse=True)
def mock_reports_store(tmp_path, monkeypatch):
    monkeypatch.setattr("services.report_repository.Config.REPORTS_DIR", tmp_path)


def test_compare_two_reports_basic():
    save_report({
        "report_metadata": {"filename": "rep1.pdf", "report_date": "2026-01-10"},
        "parameters": [
            {
                "test_name": "Hemoglobin",
                "result_value": "10.0",
                "numeric_value": 10.0,
                "unit": "g/dL",
                "reference_range": "12-16",
                "status": "Low",
            }
        ],
    })

    save_report({
        "report_metadata": {"filename": "rep2.pdf", "report_date": "2026-04-10"},
        "parameters": [
            {
                "test_name": "Hemoglobin",
                "result_value": "12.0",
                "numeric_value": 12.0,
                "unit": "g/dL",
                "reference_range": "12-16",
                "status": "Normal",
            }
        ],
    })

    result = compare_reports(["rep1.pdf", "rep2.pdf"])

    assert result["comparison_metadata"]["report_count"] == 2
    assert "Hemoglobin" in result["common_parameters"]
    assert len(result["comparison"]) == 1

    hemo_comp = result["comparison"][0]
    assert hemo_comp["parameter"] == "Hemoglobin"
    assert len(hemo_comp["measurements"]) == 2

    # Check chronological ordering
    assert hemo_comp["measurements"][0]["date"] == "2026-01-10"
    assert hemo_comp["measurements"][1]["date"] == "2026-04-10"

    # Check numerical trend
    trend = hemo_comp["trends"][0]
    assert trend["previous_value"] == 10.0
    assert trend["current_value"] == 12.0
    assert trend["absolute_change"] == 2.0
    assert trend["percentage_change"] == 20.0
    assert trend["units_compatible"] is True


def test_reference_range_preservation():
    save_report({
        "report_metadata": {"filename": "repA.pdf", "report_date": "2026-01-10"},
        "parameters": [
            {
                "test_name": "Hemoglobin",
                "result_value": "10.0",
                "numeric_value": 10.0,
                "unit": "g/dL",
                "reference_range": "12-16",
                "status": "Low",
            }
        ],
    })

    save_report({
        "report_metadata": {"filename": "repB.pdf", "report_date": "2026-04-10"},
        "parameters": [
            {
                "test_name": "Hemoglobin",
                "result_value": "11.0",
                "numeric_value": 11.0,
                "unit": "g/dL",
                "reference_range": "11.5 - 15.5",
                "status": "Low",
            }
        ],
    })

    result = compare_reports(["repA.pdf", "repB.pdf"])
    measurements = result["comparison"][0]["measurements"]

    # Verify report-specific reference ranges are preserved
    assert measurements[0]["reference_range"] == "12-16"
    assert measurements[1]["reference_range"] == "11.5 - 15.5"


def test_incompatible_units_handling():
    save_report({
        "report_metadata": {"filename": "repU1.pdf", "report_date": "2026-01-10"},
        "parameters": [
            {
                "test_name": "WBC",
                "result_value": "6000",
                "numeric_value": 6000.0,
                "unit": "/uL",
                "reference_range": "4000 - 11000",
                "status": "Normal",
            }
        ],
    })

    save_report({
        "report_metadata": {"filename": "repU2.pdf", "report_date": "2026-04-10"},
        "parameters": [
            {
                "test_name": "WBC",
                "result_value": "6.5",
                "numeric_value": 6.5,
                "unit": "10^3/uL",
                "reference_range": "4.5 - 11.0",
                "status": "Normal",
            }
        ],
    })

    result = compare_reports(["repU1.pdf", "repU2.pdf"])
    trend = result["comparison"][0]["trends"][0]

    assert trend["units_compatible"] is False
    assert trend["absolute_change"] is None
    assert trend["percentage_change"] is None


def test_validation_errors():
    with pytest.raises(ValueError) as exc1:
        compare_reports(["single.pdf"])
    assert "At least 2 reports" in str(exc1.value)

    with pytest.raises(ValueError) as exc2:
        compare_reports(["dup.pdf", "dup.pdf"])
    assert "at least 2 distinct reports" in str(exc2.value)
