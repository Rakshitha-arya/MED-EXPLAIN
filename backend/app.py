"""Flask application factory for MedExplain."""
from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from flask_cors import CORS

from config import Config
from routes.health_routes import health_bp
from routes.rag_routes import rag_bp
from routes.report_routes import report_bp


def create_app(config_object: type[Config] = Config) -> Flask:
    """Create the web application without building embeddings or indexes."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    config_object.ensure_runtime_directories()
    CORS(app, origins=app.config["CORS_ORIGINS"])

    @app.errorhandler(RequestEntityTooLarge)
    def handle_oversized_upload(_error):
        return jsonify({"error": "File size exceeds the maximum allowed upload limit."}), 413
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(rag_bp, url_prefix="/api/rag")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
