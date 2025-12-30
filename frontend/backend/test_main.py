"""
Basic tests for the prompt-ops frontend backend
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test that the server is running"""
    response = client.get("/api/configurations")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "metrics" in data
    assert "dataset_adapters" in data
    assert "strategies" in data


def test_configurations_endpoint():
    """Test the configurations endpoint returns expected structure"""
    response = client.get("/api/configurations")
    assert response.status_code == 200

    data = response.json()

    # Check models
    assert isinstance(data["models"], dict)
    assert "Llama 3.3 70B" in data["models"]

    # Check metrics
    assert isinstance(data["metrics"], dict)
    assert "Exact Match" in data["metrics"]

    # Check dataset adapters
    assert isinstance(data["dataset_adapters"], dict)
    assert "standard_json" in data["dataset_adapters"]

    # Check strategies
    assert isinstance(data["strategies"], dict)
    assert "Basic" in data["strategies"]


@patch("main.openai_api_key", "test-key")
@patch("main.client")
def test_enhance_prompt_success(mock_client):
    """Test successful prompt enhancement"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Enhanced prompt"
    mock_client.chat.completions.create.return_value = mock_response

    response = client.post("/api/enhance-prompt", json={"prompt": "Test prompt"})

    assert response.status_code == 200
    data = response.json()
    assert "optimizedPrompt" in data
    assert data["optimizedPrompt"] == "Enhanced prompt"


def test_enhance_prompt_no_api_key():
    """Test enhance prompt without API key"""
    with patch("main.openai_api_key", None):
        response = client.post("/api/enhance-prompt", json={"prompt": "Test prompt"})

        assert response.status_code == 500
        assert "OPENAI_API_KEY not configured" in response.json()["detail"]


def test_dataset_upload_invalid_json():
    """Test dataset upload with invalid JSON"""
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("test.json", "invalid json", "application/json")},
    )

    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]


def test_dataset_upload_non_array():
    """Test dataset upload with non-array JSON"""
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("test.json", '{"key": "value"}', "application/json")},
    )

    assert response.status_code == 400
    assert "must be a JSON array" in response.json()["detail"]


def test_dataset_upload_empty_array():
    """Test dataset upload with empty array"""
    response = client.post(
        "/api/datasets/upload", files={"file": ("test.json", "[]", "application/json")}
    )

    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_dataset_upload_success():
    """Test successful dataset upload"""
    test_data = [
        {"question": "What is AI?", "answer": "Artificial Intelligence"},
        {"question": "What is ML?", "answer": "Machine Learning"},
    ]

    response = client.post(
        "/api/datasets/upload",
        files={"file": ("test.json", json.dumps(test_data), "application/json")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.json"
    assert data["total_records"] == 2
    assert len(data["preview"]) == 2


def test_list_datasets():
    """Test listing datasets"""
    response = client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "datasets" in data
    assert isinstance(data["datasets"], list)


def test_options_endpoints():
    """Test CORS preflight requests"""
    endpoints = [
        "/api/enhance-prompt",
        "/api/migrate-prompt",
        "/api/configurations",
        "/api/datasets/upload",
        "/api/datasets",
    ]

    for endpoint in endpoints:
        response = client.options(endpoint)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
