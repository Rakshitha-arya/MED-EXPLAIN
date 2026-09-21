"""Lab analyzer module for numeric result parsing, reference range parsing, and classification."""
from __future__ import annotations

import re
from typing import Optional, TypedDict

# Recognized qualitative terms that must NOT be forced into Low/Normal/High numeric classification
QUALITATIVE_TERMS = {
    "positive",
    "negative",
    "reactive",
    "non-reactive",
    "nonreactive",
    "present",
    "absent",
    "normal",
    "abnormal",
    "trace",
    "clear",
    "cloudy",
    "detected",
    "not detected",
    "desirable",
    "borderline",
    "high risk",
}


class ParsedRange(TypedDict):
    min: Optional[float]
    max: Optional[float]
    kind: str  # "range", "less_than", "greater_than"


def parse_numeric_value(val_input: object) -> Optional[float]:
    """Parse a numeric float value from a string, float, or int.

    Returns None if the value is non-numeric, qualitative, or empty.
    """
    if val_input is None:
        return None
    if isinstance(val_input, (int, float)):
        return float(val_input)

    val_str = str(val_input).strip()
    if not val_str:
        return None

    clean_lower = val_str.lower()
    if clean_lower in QUALITATIVE_TERMS:
        return None

    if not any(char.isdigit() for char in val_str):
        return None

    match = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def parse_reference_range(range_input: Optional[str]) -> Optional[ParsedRange]:
    """Parse explicit numeric reference ranges into min/max thresholds.

    Supported formats:
    - Interval: "13.5 - 17.5", "13.5-17.5", "13.5 to 17.5"
    - Upper bound: "< 200", "<200", "<= 200", "less than 200"
    - Lower bound: "> 60", ">= 60", ">60", "greater than 60"

    Returns None for missing, non-numeric, qualitative, or ambiguous ranges.
    """
    if not range_input:
        return None

    raw_str = str(range_input).strip()
    if not raw_str:
        return None

    if not any(char.isdigit() for char in raw_str):
        return None

    # Upper bound (< or <=)
    less_than_match = re.match(
        r"^\s*(?:<=?|<|less\s+than)\s*([-+]?\d+(?:\.\d+)?)", raw_str, re.IGNORECASE
    )
    if less_than_match:
        try:
            max_val = float(less_than_match.group(1))
            return {"min": None, "max": max_val, "kind": "less_than"}
        except ValueError:
            return None

    # Lower bound (> or >=)
    greater_than_match = re.match(
        r"^\s*(?:>=?|>|greater\s+than)\s*([-+]?\d+(?:\.\d+)?)", raw_str, re.IGNORECASE
    )
    if greater_than_match:
        try:
            min_val = float(greater_than_match.group(1))
            return {"min": min_val, "max": None, "kind": "greater_than"}
        except ValueError:
            return None

    # Interval range (13.5 - 17.5)
    range_match = re.search(
        r"([-+]?\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*([-+]?\d+(?:\.\d+)?)",
        raw_str,
        re.IGNORECASE,
    )
    if range_match:
        try:
            low_val = float(range_match.group(1))
            high_val = float(range_match.group(2))
            if low_val <= high_val:
                return {"min": low_val, "max": high_val, "kind": "range"}
            else:
                return {"min": high_val, "max": low_val, "kind": "range"}
        except ValueError:
            return None

    return None


def classify_result(val_input: object, ref_range_input: Optional[str]) -> str:
    """Classify result as 'Low', 'Normal', 'High', or 'Unknown'.

    Rules:
    - Qualitative values (e.g. Positive/Negative) -> 'Unknown'
    - Non-numeric or missing numeric value -> 'Unknown'
    - Missing or unparseable reference range -> 'Unknown'
    - Safe numeric comparison against explicit reference range -> 'Low' | 'Normal' | 'High'
    """
    if val_input is None:
        return "Unknown"

    str_val = str(val_input).strip()
    if str_val.lower() in QUALITATIVE_TERMS:
        return "Unknown"

    numeric_val = parse_numeric_value(val_input)
    if numeric_val is None:
        return "Unknown"

    parsed_range = parse_reference_range(ref_range_input)
    if parsed_range is None:
        return "Unknown"

    kind = parsed_range["kind"]
    min_val = parsed_range["min"]
    max_val = parsed_range["max"]

    if kind == "range":
        assert min_val is not None and max_val is not None
        if numeric_val < min_val:
            return "Low"
        elif numeric_val > max_val:
            return "High"
        else:
            return "Normal"

    elif kind == "less_than":
        assert max_val is not None
        if numeric_val > max_val:
            return "High"
        else:
            return "Normal"

    elif kind == "greater_than":
        assert min_val is not None
        if numeric_val < min_val:
            return "Low"
        else:
            return "Normal"

    return "Unknown"
