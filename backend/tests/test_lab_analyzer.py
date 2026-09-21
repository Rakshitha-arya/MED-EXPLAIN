"""Tests for lab_analyzer service."""
from __future__ import annotations

from services.lab_analyzer import (
    classify_result,
    parse_numeric_value,
    parse_reference_range,
)


def test_parse_numeric_value():
    assert parse_numeric_value("13.5") == 13.5
    assert parse_numeric_value(14.0) == 14.0
    assert parse_numeric_value(" 120 mg/dL ") == 120.0
    assert parse_numeric_value("Positive") is None
    assert parse_numeric_value("Negative") is None
    assert parse_numeric_value("Normal") is None
    assert parse_numeric_value("") is None
    assert parse_numeric_value(None) is None


def test_parse_reference_range():
    # Interval range
    range1 = parse_reference_range("13.5 - 17.5")
    assert range1 is not None
    assert range1["min"] == 13.5
    assert range1["max"] == 17.5
    assert range1["kind"] == "range"

    range2 = parse_reference_range("70 to 99")
    assert range2 is not None
    assert range2["min"] == 70.0
    assert range2["max"] == 99.0

    # Upper bound
    range3 = parse_reference_range("< 200")
    assert range3 is not None
    assert range3["min"] is None
    assert range3["max"] == 200.0
    assert range3["kind"] == "less_than"

    # Lower bound
    range4 = parse_reference_range("> 60")
    assert range4 is not None
    assert range4["min"] == 60.0
    assert range4["max"] is None
    assert range4["kind"] == "greater_than"

    # Non-numeric / ambiguous
    assert parse_reference_range(None) is None
    assert parse_reference_range("") is None
    assert parse_reference_range("Desirable") is None
    assert parse_reference_range("Negative") is None


def test_classify_result_numeric_bounds():
    # Range interval: 13.5 - 17.5
    assert classify_result("12.0", "13.5 - 17.5") == "Low"
    assert classify_result("15.0", "13.5 - 17.5") == "Normal"
    assert classify_result("13.5", "13.5 - 17.5") == "Normal"
    assert classify_result("17.5", "13.5 - 17.5") == "Normal"
    assert classify_result("18.5", "13.5 - 17.5") == "High"

    # Upper bound (< 200)
    assert classify_result("150", "< 200") == "Normal"
    assert classify_result("200", "< 200") == "Normal"
    assert classify_result("250", "< 200") == "High"

    # Lower bound (> 60)
    assert classify_result("50", "> 60") == "Low"
    assert classify_result("60", "> 60") == "Normal"
    assert classify_result("75", "> 60") == "Normal"


def test_missing_reference_range_returns_unknown():
    assert classify_result("14.0", None) == "Unknown"
    assert classify_result("14.0", "") == "Unknown"
    assert classify_result("14.0", "Desirable") == "Unknown"


def test_qualitative_result_returns_unknown():
    assert classify_result("Positive", "Negative") == "Unknown"
    assert classify_result("Negative", "Negative") == "Unknown"
    assert classify_result("Reactive", "Non-Reactive") == "Unknown"
    assert classify_result("Normal", "Normal") == "Unknown"
