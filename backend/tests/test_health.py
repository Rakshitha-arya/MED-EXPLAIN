from app import create_app


def test_health_endpoint_returns_ok():
    app = create_app()
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "medexplain-backend"}
