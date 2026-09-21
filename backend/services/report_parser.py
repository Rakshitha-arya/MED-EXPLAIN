"""Report parser service for extracting report date and structured lab parameters."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services.lab_analyzer import classify_result, parse_numeric_value

DATE_PATTERNS = [
    r"(?:Report\s+Date|Collection\s+Date|Date|Collected):\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
    r"(?:Report\s+Date|Collection\s+Date|Date|Collected):\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})",
    r"(?:Report\s+Date|Collection\s+Date|Date|Collected):\s*([0-9]{1,2}-[A-Za-z]{3}-[0-9]{2,4})",
    r"Date:\s*([^\n\r]+)",
]


def extract_report_date(text: str) -> Optional[str]:
    """Extract report date from report text if clearly present."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            date_str = re.sub(r"[^\w/\-\s].*$", "", date_str).strip()
            if date_str:
                return date_str
    return None


def parse_line_for_parameter(line: str) -> Optional[Dict[str, Any]]:
    """Attempt to parse a single line into a lab test parameter dict."""
    cleaned_line = line.strip()
    if (
        not cleaned_line
        or cleaned_line.startswith("--- Page")
        or cleaned_line.lower().startswith("patient")
        or cleaned_line.lower().startswith("doctor")
    ):
        return None

    # Pattern 1: Colon-separated key-value with optional unit and reference range
    # e.g. "Hemoglobin: 14.2 g/dL (13.5 - 17.5)" or "HBsAg: Positive (Negative)"
    colon_match = re.match(
        r"^(?P<name>[A-Za-z0-9\s/_\-\(\)]+?):\s*"
        r"(?P<val>[-+]?\d+(?:\.\d+)?|[A-Za-z]+)\s*"
        r"(?:(?P<unit>[A-Za-z0-9/%^\^\-\.\_µ]+)\s*)?"
        r"(?:[\(\[]?\s*(?:Ref|Reference|Range|Interval)?:?\s*(?P<ref>[<>]?\s*[-+]?\d+(?:\.\d+)?(?:\s*(?:-|to|–|—)\s*[-+]?\d+(?:\.\d+)?)?|[A-Za-z]+)?[\)\]]?)?",
        cleaned_line,
        re.IGNORECASE,
    )

    if colon_match:
        name = colon_match.group("name").strip()
        val_str = colon_match.group("val").strip()
        unit_str = (
            colon_match.group("unit").strip()
            if colon_match.group("unit")
            else None
        )
        ref_str = (
            colon_match.group("ref").strip() if colon_match.group("ref") else None
        )

        if name.lower() in (
            "date",
            "report date",
            "collection date",
            "patient",
            "doctor",
            "page",
        ):
            return None

        num_val = parse_numeric_value(val_str)
        status = classify_result(val_str, ref_str)

        return {
            "test_name": name,
            "result_value": val_str,
            "numeric_value": num_val,
            "unit": unit_str,
            "reference_range": ref_str,
            "source_text": cleaned_line,
            "status": status,
        }

    # Pattern 2: Tabular / whitespace delimited format
    # e.g. "Hemoglobin    14.2    g/dL    13.5 - 17.5"
    tabular_match = re.match(
        r"^(?P<name>[A-Za-z0-9\s/_\-\(\)]+?)\s{2,}"
        r"(?P<val>[-+]?\d+(?:\.\d+)?|[A-Za-z]+)"
        r"(?:\s+(?P<unit>[A-Za-z0-9/%^\^\-\.\_µ]+))?"
        r"(?:\s+(?P<ref>[<>]?\s*[-+]?\d+(?:\.\d+)?(?:\s*(?:-|to|–|—)\s*[-+]?\d+(?:\.\d+)?)?|[A-Za-z]+))?$",
        cleaned_line,
    )

    if tabular_match:
        name = tabular_match.group("name").strip()
        val_str = tabular_match.group("val").strip()
        unit_str = (
            tabular_match.group("unit").strip()
            if tabular_match.group("unit")
            else None
        )
        ref_str = (
            tabular_match.group("ref").strip()
            if tabular_match.group("ref")
            else None
        )

        if name.lower() in (
            "test",
            "parameter",
            "name",
            "result",
            "units",
            "reference",
        ):
            return None

        num_val = parse_numeric_value(val_str)
        status = classify_result(val_str, ref_str)

        return {
            "test_name": name,
            "result_value": val_str,
            "numeric_value": num_val,
            "unit": unit_str,
            "reference_range": ref_str,
            "source_text": cleaned_line,
            "status": status,
        }

    return None


def parse_report_text(text: str) -> Dict[str, Any]:
    """Parse medical report text into structured metadata and parameter list."""
    if not text:
        return {"report_date": None, "parameters": []}

    report_date = extract_report_date(text)
    parameters: List[Dict[str, Any]] = []

    lines = text.splitlines()
    for line in lines:
        param = parse_line_for_parameter(line)
        if param:
            parameters.append(param)

    return {"report_date": report_date, "parameters": parameters}
