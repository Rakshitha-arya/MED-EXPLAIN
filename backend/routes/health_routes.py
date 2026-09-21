"""Non-medical operational endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """Return a minimal readiness response without accessing medical records."""
    return jsonify({"status": "ok", "service": "medexplain-backend"})
