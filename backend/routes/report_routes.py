"""API routes for medical report upload, analysis, comparison, trends, and chat."""
from __future__ import annotations

from pathlib import Path
import re
from flask import Blueprint, jsonify, request

from config import Config
from services.llm_service import generate_response as llm_generate_response
from services.rag_service import retrieve_for_report
from services.report_comparison import compare_reports, get_parameter_trends
from services.report_ingestion import IngestionError, ingest_report
from services.report_parser import parse_report_text
from services.report_repository import (
    get_report,
    list_reports,
    save_report,
)

report_bp = Blueprint("reports", __name__)

DISCLAIMER_TEXT = (
    "This analysis is for educational and informational purposes only. "
    "It is not a diagnostic tool or medical advice."
)
_REPORT_FILE_PATTERN = re.compile(r"^[a-f0-9]{32}(?:\.(?:pdf|png|jpg|jpeg))?$", re.IGNORECASE)


def _internal_error(operation: str):
    """Return a safe client error without exposing exception details or paths."""
    return jsonify({"error": f"Unable to {operation}. Please try again later."}), 500


def _find_report_file(report_id: str) -> Path | None:
    """Find local report file in UPLOAD_DIR by filename or UUID prefix."""
    if not _REPORT_FILE_PATTERN.fullmatch(str(report_id or "")):
        return None
    target_path = Config.UPLOAD_DIR / report_id
    if target_path.is_file():
        return target_path

    for ext in (".pdf", ".png", ".jpg", ".jpeg"):
        candidate = Config.UPLOAD_DIR / f"{report_id}{ext}"
        if candidate.is_file():
            return candidate

    return None


@report_bp.route("", methods=["GET"])
@report_bp.route("/", methods=["GET"])
def get_reports_list():
    """List all available analyzed reports in repository (summary metadata)."""
    try:
        reports = list_reports()
        return jsonify({"reports": reports, "count": len(reports)}), 200
    except Exception:
        return _internal_error("retrieve reports")


@report_bp.route("/upload", methods=["POST"])
def upload_report():
    """Upload and process a medical report file (PDF, JPG, PNG)."""
    if "file" not in request.files and "report" not in request.files:
        return jsonify({"error": "No file part in multipart request."}), 400

    file_obj = request.files.get("file") or request.files.get("report")
    if not file_obj or file_obj.filename == "":
        return jsonify({"error": "No file selected for upload."}), 400

    try:
        file_bytes = file_obj.read()
        ingested_data = ingest_report(file_bytes, file_obj.filename)
        parsed_data = parse_report_text(ingested_data["extracted_text"])

        response_payload = {
            "report_metadata": {
                "filename": ingested_data["filename"],
                "original_filename": ingested_data["original_filename"],
                "file_type": ingested_data["file_type"],
                "page_count": ingested_data["page_count"],
                "report_date": parsed_data.get("report_date"),
            },
            "extraction_method": ingested_data["extraction_method"],
            "extracted_text": ingested_data["extracted_text"],
            "parameters": parsed_data.get("parameters", []),
            "disclaimer": DISCLAIMER_TEXT,
        }

        # Save record to repository
        save_report(response_payload)

        return jsonify(response_payload), 200

    except IngestionError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except Exception:
        return _internal_error("process the report")


@report_bp.route("/analyze", methods=["POST"])
def analyze_report():
    """Upload and analyze a report with MedQuAD report-aware retrieval."""
    if "file" not in request.files and "report" not in request.files:
        return jsonify({"error": "No file part in multipart request."}), 400

    file_obj = request.files.get("file") or request.files.get("report")
    if not file_obj or file_obj.filename == "":
        return jsonify({"error": "No file selected for analysis."}), 400

    try:
        file_bytes = file_obj.read()
        ingested_data = ingest_report(file_bytes, file_obj.filename)
        parsed_data = parse_report_text(ingested_data["extracted_text"])

        parameters = parsed_data.get("parameters", [])

        retrieved_knowledge = retrieve_for_report(
            extracted_text=ingested_data["extracted_text"],
            parameters=parameters,
            user_question=None,
            top_k=3,
        )

        response_payload = {
            "report_metadata": {
                "filename": ingested_data["filename"],
                "original_filename": ingested_data["original_filename"],
                "file_type": ingested_data["file_type"],
                "page_count": ingested_data["page_count"],
                "report_date": parsed_data.get("report_date"),
            },
            "extraction_method": ingested_data["extraction_method"],
            "extracted_text": ingested_data["extracted_text"],
            "parameters": parameters,
            "retrieved_knowledge": retrieved_knowledge,
            "disclaimer": DISCLAIMER_TEXT,
        }

        # Save record to repository
        save_report(response_payload)

        return jsonify(response_payload), 200

    except IngestionError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except Exception:
        return _internal_error("analyze the report")


@report_bp.route("/compare", methods=["POST"])
def compare_reports_endpoint():
    """Compare multiple uploaded medical reports across dates."""
    if not request.is_json:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    data = request.get_json() or {}
    report_ids = data.get("report_ids")

    if not report_ids or not isinstance(report_ids, list):
        return jsonify(
            {"error": "Field 'report_ids' must be a list containing at least 2 report IDs."}
        ), 400

    if len(report_ids) < 2:
        return jsonify({"error": "At least 2 report IDs are required for comparison."}), 400

    try:
        result = compare_reports(report_ids)
        return jsonify(result), 200
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception:
        return _internal_error("compare reports")


@report_bp.route("/trends", methods=["GET"])
def get_trends_endpoint():
    """Retrieve chronological measurements for a given parameter across all stored reports."""
    parameter_name = request.args.get("parameter")
    if not parameter_name or not str(parameter_name).strip():
        return jsonify({"error": "Query parameter 'parameter' is required."}), 400

    try:
        result = get_parameter_trends(parameter_name)
        return jsonify(result), 200
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception:
        return _internal_error("retrieve trends")


@report_bp.route("/<report_id>/explain", methods=["POST"])
def explain_report(report_id: str):
    """Generate a patient-friendly educational LLM explanation for an uploaded report."""
    report_path = _find_report_file(report_id)
    stored_record = get_report(report_id)

    if not report_path and not stored_record:
        return jsonify({"error": f"Report '{report_id}' not found."}), 404

    data = request.get_json(silent=True) or {}
    user_question = data.get("question") or "Can you explain my medical report results in simple terms?"

    try:
        if stored_record:
            extracted_text = stored_record.get("extracted_text", "")
            parameters = stored_record.get("parameters", [])
            metadata = {
                "filename": stored_record.get("filename"),
                "original_filename": stored_record.get("original_filename"),
                "file_type": stored_record.get("file_type"),
                "page_count": stored_record.get("page_count", 1),
                "report_date": stored_record.get("report_date"),
            }
        else:
            file_bytes = report_path.read_bytes()
            ingested_data = ingest_report(file_bytes, report_path.name)
            parsed_data = parse_report_text(ingested_data["extracted_text"])
            extracted_text = ingested_data["extracted_text"]
            parameters = parsed_data.get("parameters", [])
            metadata = {
                "filename": ingested_data["filename"],
                "original_filename": ingested_data["original_filename"],
                "file_type": ingested_data["file_type"],
                "page_count": ingested_data["page_count"],
                "report_date": parsed_data.get("report_date"),
            }

        report_context = {
            "report_metadata": metadata,
            "extracted_text": extracted_text,
            "parameters": parameters,
        }

        retrieved_context = retrieve_for_report(
            extracted_text=extracted_text,
            parameters=parameters,
            user_question=str(user_question).strip(),
            top_k=3,
        )

        llm_result = llm_generate_response(
            report_context=report_context,
            retrieved_context=retrieved_context,
            user_question=str(user_question).strip(),
        )

        return (
            jsonify(
                {
                    "status": llm_result.get("status", "not_configured"),
                    "question": str(user_question).strip(),
                    "report_context": report_context,
                    "retrieved_context": retrieved_context,
                    "answer": llm_result.get("answer"),
                    "disclaimer": DISCLAIMER_TEXT,
                }
            ),
            200,
        )

    except IngestionError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except Exception:
        return _internal_error("generate an explanation")


@report_bp.route("/<report_id>/chat", methods=["POST"])
def chat_with_report(report_id: str):
    """Report-aware chat endpoint combining report context, RAG retrieval, and LLM explanation."""
    if not request.is_json:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    data = request.get_json() or {}
    user_question = data.get("question")
    if not user_question or not str(user_question).strip():
        return jsonify({"error": "Question is required and cannot be empty."}), 400

    report_path = _find_report_file(report_id)
    stored_record = get_report(report_id)

    if not report_path and not stored_record:
        return jsonify({"error": f"Report '{report_id}' not found."}), 404

    try:
        if stored_record:
            extracted_text = stored_record.get("extracted_text", "")
            parameters = stored_record.get("parameters", [])
            metadata = {
                "filename": stored_record.get("filename"),
                "original_filename": stored_record.get("original_filename"),
                "file_type": stored_record.get("file_type"),
                "page_count": stored_record.get("page_count", 1),
                "report_date": stored_record.get("report_date"),
            }
        else:
            file_bytes = report_path.read_bytes()
            ingested_data = ingest_report(file_bytes, report_path.name)
            parsed_data = parse_report_text(ingested_data["extracted_text"])
            extracted_text = ingested_data["extracted_text"]
            parameters = parsed_data.get("parameters", [])
            metadata = {
                "filename": ingested_data["filename"],
                "original_filename": ingested_data["original_filename"],
                "file_type": ingested_data["file_type"],
                "page_count": ingested_data["page_count"],
                "report_date": parsed_data.get("report_date"),
            }

        report_context = {
            "report_metadata": metadata,
            "extracted_text": extracted_text,
            "parameters": parameters,
        }

        retrieved_knowledge = retrieve_for_report(
            extracted_text=extracted_text,
            parameters=parameters,
            user_question=str(user_question).strip(),
            top_k=3,
        )

        llm_result = llm_generate_response(
            report_context=report_context,
            retrieved_context=retrieved_knowledge,
            user_question=str(user_question).strip(),
        )

        return (
            jsonify(
                {
                    "status": llm_result.get("status", "not_configured"),
                    "report_id": report_id,
                    "question": str(user_question).strip(),
                    "report_context": report_context,
                    "retrieved_knowledge": retrieved_knowledge,
                    "llm_status": llm_result.get("llm_status"),
                    "provider": llm_result.get("provider"),
                    "answer": llm_result.get("answer"),
                    "prepared_prompt": llm_result.get("prepared_prompt"),
                    "disclaimer": DISCLAIMER_TEXT,
                }
            ),
            200,
        )

    except IngestionError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except Exception:
        return _internal_error("process the chat request")
