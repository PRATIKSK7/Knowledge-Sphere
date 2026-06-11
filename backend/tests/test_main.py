import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_login_error():
    # Attempting to login with incorrect credentials should fail
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "notexist@knowledgesphere.ai", "password": "wrongpassword"}
    )
    assert response.status_code == 401
