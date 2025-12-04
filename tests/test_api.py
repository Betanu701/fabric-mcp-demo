"""
Basic tests for the FastAPI backend
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_list_agents():
    """Test listing agents"""
    response = client.get("/api/agents", headers={"X-Tenant-ID": "default"})
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "total" in data


def test_chat_message():
    """Test sending a chat message"""
    response = client.post(
        "/api/chat",
        headers={"X-Tenant-ID": "default"},
        json={"message": "Hello, how can you help?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "agent_id" in data
    assert "conversation_id" in data
