"""Tests for report_parser service."""
from __future__ import annotations

from services.report_parser import extract_report_date, parse_report_text


def test_extract_report_date():
    assert extract_report_date("Date: 2026-09-18\nHemoglobin: 14.2") == "2026-09-18"
    assert extract_report_date("Report Date: 09/18/2026\nResult: 100") == "09/18/2026"
    assert extract_report_date("Collection Date: 18-Sep-2026") == "18-Sep-2026"
    assert extract_report_date("No date header present in report text") is None


def test_parse_report_text_synthetic():
    report_text = """
Date: 2026-09-18
Patient Name: Jane Doe
Hemoglobin: 14.2 g/dL (13.5 - 17.5)
White Blood Cell Count: 12.5 x10^3/uL (4.5 - 11.0)
Platelets: 120 10^3/uL (150 - 450)
Total Cholesterol: 220 mg/dL (< 200)
HBsAg: Positive (Negative)
"""
    parsed = parse_report_text(report_text)
    assert parsed["report_date"] == "2026-09-18"

    params = parsed["parameters"]
    assert len(params) >= 4

    # Hemoglobin -> Normal
    hemo = next((p for p in params if "Hemoglobin" in p["test_name"]), None)
    assert hemo is not None
    assert hemo["result_value"] == "14.2"
    assert hemo["numeric_value"] == 14.2
    assert hemo["unit"] == "g/dL"
    assert hemo["reference_range"] == "13.5 - 17.5"
    assert hemo["status"] == "Normal"

    # White Blood Cell Count -> High
    wbc = next((p for p in params if "White Blood Cell" in p["test_name"]), None)
    assert wbc is not None
    assert wbc["numeric_value"] == 12.5
    assert wbc["status"] == "High"

    # HBsAg -> Unknown
    hbsag = next((p for p in params if "HBsAg" in p["test_name"]), None)
    assert hbsag is not None
    assert hbsag["status"] == "Unknown"


def test_malformed_report_produces_no_invented_parameters():
    parsed = parse_report_text("unstructured scan artifact @@ %%\nno laboratory fields here")
    assert parsed["report_date"] is None
    assert parsed["parameters"] == []
