from unittest.mock import patch


def test_failed_dependency_returns_503_without_error_details(client):
    with patch(
        "apps.operations.views.infrastructure_status", return_value={"status": "unavailable"}
    ):
        response = client.get("/health/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
