"""Report repository service for persisting, listing, and retrieving analyzed report records."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import Config


def _get_reports_dir() -> Path:
    """Ensure and return the reports data store directory."""
    Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return Config.REPORTS_DIR


_REPORT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(?:\.(?:pdf|png|jpg|jpeg))?$")


def _sanitize_report_id(report_id: str) -> str:
    """Return a generated report ID, rejecting path-like or untrusted values."""
    value = str(report_id or "").strip()
    if not _REPORT_ID_PATTERN.fullmatch(value):
        raise ValueError("Invalid report identifier.")
    return value


def save_report(report_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Persist an analyzed report record JSON to REPORTS_DIR.

    Metadata fields stored:
    - report_id
    - filename
    - original_filename
    - report_date (None / 'Unknown' if not extracted; do NOT substitute upload time)
    - file_type
    - extraction_method
    - page_count
    - parameters
    - extracted_text
    - created_at
    """
    meta = report_payload.get("report_metadata", {})
    filename = meta.get("filename") or report_payload.get("filename")
    if not filename:
        raise ValueError("Cannot save report without a valid filename or report_id.")

    report_id = _sanitize_report_id(filename)
    reports_dir = _get_reports_dir()
    json_path = reports_dir / f"{report_id}.json"

    parameters = report_payload.get("parameters", [])
    report_date = meta.get("report_date")

    record = {
        "report_id": report_id,
        "filename": filename,
        "original_filename": meta.get("original_filename") or filename,
        "file_type": meta.get("file_type", "pdf"),
        "extraction_method": report_payload.get("extraction_method", "pdf_text"),
        "page_count": meta.get("page_count", 1),
        "report_date": report_date if report_date and str(report_date).strip() else None,
        "extracted_text": report_payload.get("extracted_text", ""),
        "parameters": parameters,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Failed to save report record to repository: {exc}") from exc

    return record


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single report record by report_id."""
    try:
        clean_id = _sanitize_report_id(report_id)
    except ValueError:
        return None
    reports_dir = _get_reports_dir()
    json_path = reports_dir / f"{clean_id}.json"

    if not json_path.is_file():
        return None

    try:
        content = json_path.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception:
        return None


def list_reports() -> List[Dict[str, Any]]:
    """List all available stored reports, returning safe summary metadata."""
    reports_dir = _get_reports_dir()
    summary_list = []

    for json_path in reports_dir.glob("*.json"):
        try:
            content = json_path.read_text(encoding="utf-8")
            data = json.loads(content)
            params = data.get("parameters", [])
            summary_list.append(
                {
                    "report_id": data.get("report_id", json_path.stem),
                    "filename": data.get("filename"),
                    "original_filename": data.get("original_filename"),
                    "file_type": data.get("file_type"),
                    "report_date": data.get("report_date"),
                    "created_at": data.get("created_at"),
                    "parameter_count": len(params) if isinstance(params, list) else 0,
                }
            )
        except Exception:
            continue

    # Sort reports by report_date descending, falling back to created_at
    def sort_key(item: Dict[str, Any]) -> str:
        return str(item.get("report_date") or item.get("created_at") or "")

    summary_list.sort(key=sort_key, reverse=True)
    return summary_list


def get_multiple_reports(report_ids: List[str]) -> List[Dict[str, Any]]:
    """Retrieve multiple reports by their report IDs."""
    results = []
    missing = []
    for rid in report_ids:
        rep = get_report(rid)
        if rep:
            results.append(rep)
        else:
            missing.append(rid)

    if missing:
        raise ValueError(f"Report(s) not found: {', '.join(missing)}")

    return results


def delete_report(report_id: str) -> bool:
    """Delete a report record JSON and its upload binary if present."""
    try:
        clean_id = _sanitize_report_id(report_id)
    except ValueError:
        return False
    reports_dir = _get_reports_dir()
    json_path = reports_dir / f"{clean_id}.json"

    deleted = False
    if json_path.is_file():
        json_path.unlink()
        deleted = True

    # Check upload dir
    upload_stem = Path(clean_id).stem
    for ext in (".pdf", ".png", ".jpg", ".jpeg"):
        upload_file = Config.UPLOAD_DIR / f"{upload_stem}{ext}"
        if upload_file.is_file():
            upload_file.unlink()

    return deleted
