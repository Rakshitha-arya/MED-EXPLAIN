"""Multi-report comparison service for tracking lab parameter trends across report dates."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.lab_analyzer import parse_numeric_value
from services.report_repository import get_multiple_reports

COMPARISON_DISCLAIMER = (
    "This comparison shows numerical changes between uploaded reports. "
    "It does not provide a medical diagnosis or treatment recommendation."
)

# Safe normalization map for synonymous common lab parameter test names
NAME_NORMALIZATION_MAP = {
    "hgb": "hemoglobin",
    "hb": "hemoglobin",
    "wbc": "white blood cell count",
    "rbc": "red blood cell count",
    "plt": "platelets",
    "platelet count": "platelets",
    "fbs": "fasting blood sugar",
    "fasting glucose": "fasting blood sugar",
    "fast glucose": "fasting blood sugar",
}


def _normalize_parameter_name(name: str) -> str:
    """Normalize parameter string safely for comparison grouping."""
    clean = str(name).strip().lower()
    return NAME_NORMALIZATION_MAP.get(clean, clean)


def _parse_date_sort_key(date_str: Optional[str]) -> Tuple[int, str]:
    """Parse report date for chronological sorting (dated reports first, unknown dates last)."""
    if not date_str or not str(date_str).strip():
        return (1, "9999-99-99")

    clean = str(date_str).strip()
    try:
        # Try standard YYYY-MM-DD
        dt = datetime.strptime(clean, "%Y-%m-%d")
        return (0, dt.strftime("%Y-%m-%d"))
    except ValueError:
        pass

    try:
        # Try MM/DD/YYYY
        dt = datetime.strptime(clean, "%m/%d/%Y")
        return (0, dt.strftime("%Y-%m-%d"))
    except ValueError:
        pass

    try:
        # Try DD-Mon-YYYY
        dt = datetime.strptime(clean, "%d-%b-%Y")
        return (0, dt.strftime("%Y-%m-%d"))
    except ValueError:
        pass

    return (0, clean)


def _are_units_compatible(unit1: Optional[str], unit2: Optional[str]) -> bool:
    """Check if two units are compatible for direct numeric change calculation."""
    if unit1 is None and unit2 is None:
        return True
    if not unit1 or not unit2:
        return False
    u1 = str(unit1).strip().lower()
    u2 = str(unit2).strip().lower()
    return u1 == u2


def compare_reports(report_ids: List[str]) -> Dict[str, Any]:
    """Compare multiple medical reports and calculate parameter trends across dates.

    Input: List of report IDs.
    Returns structured comparison object with:
    - selected_reports
    - common_parameters
    - comparison (parameter, unit, measurements, trends)
    - comparison_metadata
    - disclaimer
    """
    if not report_ids or len(report_ids) < 2:
        raise ValueError("At least 2 reports are required for comparison.")

    # Deduplicate report_ids preserving order
    unique_ids: List[str] = []
    for rid in report_ids:
        if rid and rid not in unique_ids:
            unique_ids.append(rid)

    if len(unique_ids) < 2:
        raise ValueError("Comparison requires at least 2 distinct reports.")

    raw_reports = get_multiple_reports(unique_ids)

    # Sort reports chronologically by report_date
    sorted_reports = sorted(
        raw_reports, key=lambda r: _parse_date_sort_key(r.get("report_date"))
    )

    selected_reports_summary = []
    for r in sorted_reports:
        params = r.get("parameters", [])
        selected_reports_summary.append(
            {
                "report_id": r.get("report_id"),
                "filename": r.get("filename"),
                "original_filename": r.get("original_filename"),
                "report_date": r.get("report_date") or "Unknown",
                "parameter_count": len(params) if isinstance(params, list) else 0,
            }
        )

    # Group measurements by normalized parameter name
    grouped_params: Dict[str, List[Dict[str, Any]]] = {}
    display_names: Dict[str, str] = {}

    for r in sorted_reports:
        rep_id = r.get("report_id")
        rep_date = r.get("report_date") or "Unknown"
        params = r.get("parameters", [])

        if isinstance(params, list):
            for p in params:
                raw_name = p.get("test_name")
                if not raw_name:
                    continue

                norm_key = _normalize_parameter_name(raw_name)
                if norm_key not in display_names:
                    display_names[norm_key] = raw_name

                val_str = p.get("result_value")
                num_val = p.get("numeric_value")
                if num_val is None and val_str is not None:
                    num_val = parse_numeric_value(val_str)

                meas = {
                    "report_id": rep_id,
                    "date": rep_date,
                    "value": num_val,
                    "result_value": val_str,
                    "unit": p.get("unit"),
                    "reference_range": p.get("reference_range") or "Not specified",
                    "status": p.get("status", "Unknown"),
                    "source_text": p.get("source_text", ""),
                }

                if norm_key not in grouped_params:
                    grouped_params[norm_key] = []
                grouped_params[norm_key].append(meas)

    # Filter common parameters (present in 2 or more reports) and all compared parameters
    common_keys = [
        k for k, list_meas in grouped_params.items() if len(list_meas) >= 2
    ]
    common_display_names = [display_names[k] for k in common_keys]

    comparison_results = []
    for norm_key, measurements in grouped_params.items():
        disp_name = display_names[norm_key]
        primary_unit = next(
            (m["unit"] for m in measurements if m.get("unit")), None
        )

        trends = []
        # Calculate consecutive measurement trends
        for i in range(len(measurements) - 1):
            prev_m = measurements[i]
            curr_m = measurements[i + 1]

            prev_val = prev_m.get("value")
            curr_val = curr_m.get("value")
            units_compat = _are_units_compatible(
                prev_m.get("unit"), curr_m.get("unit")
            )

            if (
                prev_val is not None
                and curr_val is not None
                and units_compat
            ):
                abs_change = round(curr_val - prev_val, 2)
                pct_change = (
                    round(((curr_val - prev_val) / prev_val) * 100, 2)
                    if prev_val != 0
                    else None
                )
                trends.append(
                    {
                        "from_date": prev_m.get("date"),
                        "to_date": curr_m.get("date"),
                        "previous_value": prev_val,
                        "current_value": curr_val,
                        "absolute_change": abs_change,
                        "percentage_change": pct_change,
                        "units_compatible": True,
                    }
                )
            else:
                trends.append(
                    {
                        "from_date": prev_m.get("date"),
                        "to_date": curr_m.get("date"),
                        "previous_value": prev_val,
                        "current_value": curr_val,
                        "absolute_change": None,
                        "percentage_change": None,
                        "units_compatible": False,
                        "note": "Incompatible units or non-numeric values",
                    }
                )

        comparison_results.append(
            {
                "parameter": disp_name,
                "unit": primary_unit,
                "is_common": len(measurements) >= 2,
                "measurements": measurements,
                "trends": trends,
            }
        )

    # Sort comparison list by common parameters first
    comparison_results.sort(key=lambda x: (not x["is_common"], x["parameter"]))

    return {
        "comparison_metadata": {
            "report_count": len(sorted_reports),
            "compared_at": datetime.now(timezone.utc).isoformat(),
        },
        "selected_reports": selected_reports_summary,
        "common_parameters": common_display_names,
        "comparison": comparison_results,
        "disclaimer": COMPARISON_DISCLAIMER,
    }


def get_parameter_trends(parameter_name: str) -> Dict[str, Any]:
    """Retrieve chronological measurements for a specific parameter across all stored reports."""
    from services.report_repository import list_reports, get_report

    if not parameter_name or not str(parameter_name).strip():
        raise ValueError("Parameter name is required.")

    norm_target = _normalize_parameter_name(parameter_name)
    all_reports = list_reports()

    measurements = []
    display_name = parameter_name.strip()

    for r_summary in all_reports:
        rep_id = r_summary.get("report_id")
        full_report = get_report(rep_id)
        if not full_report:
            continue

        rep_date = full_report.get("report_date") or "Unknown"
        params = full_report.get("parameters", [])

        if isinstance(params, list):
            for p in params:
                tname = p.get("test_name")
                if tname and _normalize_parameter_name(tname) == norm_target:
                    display_name = tname
                    val_str = p.get("result_value")
                    num_val = p.get("numeric_value")
                    if num_val is None and val_str is not None:
                        num_val = parse_numeric_value(val_str)

                    measurements.append(
                        {
                            "report_id": rep_id,
                            "date": rep_date,
                            "value": num_val,
                            "result_value": val_str,
                            "unit": p.get("unit"),
                            "reference_range": p.get("reference_range") or "Not specified",
                            "status": p.get("status", "Unknown"),
                        }
                    )

    # Sort chronologically by date
    measurements.sort(key=lambda m: _parse_date_sort_key(m.get("date")))

    return {
        "parameter": display_name,
        "measurement_count": len(measurements),
        "measurements": measurements,
        "disclaimer": COMPARISON_DISCLAIMER,
    }
