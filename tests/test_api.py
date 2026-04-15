import pytest


class TestHealthEndpoint:
    def test_health_check(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestAuthEndpoints:
    def test_auth_status_returns_structure(self, api_client):
        response = api_client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_authenticated" in data
        assert "email" in data

    def test_logout_returns_success(self, api_client):
        response = api_client.post("/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestSubscriptionEndpoints:
    def test_list_subscriptions_returns_list(self, api_client):
        response = api_client.get("/subscriptions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_subscription_not_found(self, api_client):
        response = api_client.get("/subscriptions/nonexistent-id-12345")
        assert response.status_code == 404

    def test_unsubscribe_not_found(self, api_client):
        response = api_client.post("/subscriptions/nonexistent-id-12345/unsubscribe")
        assert response.status_code == 404

    def test_delete_subscription_not_found(self, api_client):
        response = api_client.delete("/subscriptions/nonexistent-id-12345")
        assert response.status_code == 404

    def test_generate_description_subscription_not_found(self, api_client):
        response = api_client.post(
            "/subscriptions/nonexistent-id-12345/generate-description",
            json={"emails": []},
        )
        assert response.status_code == 404


class TestScanEndpoints:
    def test_scan_requires_authentication(self, api_client):
        response = api_client.post("/scan", json={"days": 30})
        assert response.status_code == 401

    def test_scan_status_returns_structure(self, api_client):
        response = api_client.get("/scan/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_scanning" in data
        assert "subscriptions_found" in data
        assert "messages_processed" in data
        assert "last_scan_date" in data

    def test_scan_with_invalid_days(self, api_client):
        response = api_client.post("/scan", json={"days": 45})
        assert response.status_code == 422
