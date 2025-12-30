"""
Unit tests for routes/datasets.py
"""

import json
import os
from unittest.mock import Mock, patch

import pytest


class TestDatasetsRoutes:
    """Tests for dataset routes."""

    def test_upload_dataset_success(self, client, sample_dataset):
        """Test successful dataset upload."""
        response = client.post(
            "/api/datasets/upload",
            files={
                "file": ("test.json", json.dumps(sample_dataset), "application/json")
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.json"
        assert data["total_records"] == 3
        assert len(data["preview"]) == 3

    def test_upload_dataset_invalid_json(self, client):
        """Test uploading invalid JSON."""
        response = client.post(
            "/api/datasets/upload",
            files={"file": ("bad.json", "not valid json{", "application/json")},
        )

        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]

    def test_upload_dataset_non_array(self, client):
        """Test uploading non-array JSON."""
        response = client.post(
            "/api/datasets/upload",
            files={
                "file": ("obj.json", json.dumps({"key": "value"}), "application/json")
            },
        )

        assert response.status_code == 400
        assert "must be a JSON array" in response.json()["detail"]

    def test_upload_dataset_empty_array(self, client):
        """Test uploading empty array."""
        response = client.post(
            "/api/datasets/upload",
            files={"file": ("empty.json", "[]", "application/json")},
        )

        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]

    def test_upload_non_json_file(self, client):
        """Test uploading non-JSON file."""
        response = client.post(
            "/api/datasets/upload",
            files={"file": ("test.txt", "some text", "text/plain")},
        )

        assert response.status_code == 400
        assert "Only JSON files" in response.json()["detail"]

    def test_list_datasets(self, client):
        """Test listing datasets."""
        response = client.get("/api/datasets")

        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
        assert isinstance(data["datasets"], list)

    @patch("routes.datasets.DatasetAnalyzer")
    def test_analyze_dataset(
        self, mock_analyzer, client, sample_dataset, temp_upload_dir
    ):
        """Test dataset analysis endpoint."""
        # Setup mock analyzer
        mock_instance = Mock()
        mock_instance.analyze_fields.return_value = {
            "fields": [{"name": "question", "type": "string"}],
            "sample_values": {"question": ["Sample question"]},
            "field_mappings": {"question": "question"},
            "use_case": "qa",
        }
        mock_analyzer.return_value = mock_instance

        # Create test dataset
        dataset_path = os.path.join(temp_upload_dir, "test.json")
        with open(dataset_path, "w") as f:
            json.dump(sample_dataset, f)

        with patch("routes.datasets.UPLOAD_DIR", temp_upload_dir):
            response = client.post("/api/datasets/analyze/test.json")

            assert response.status_code == 200
            data = response.json()
            assert "fields" in data

    def test_delete_dataset(self, client, sample_dataset, temp_upload_dir):
        """Test dataset deletion."""
        # Create test dataset
        dataset_path = os.path.join(temp_upload_dir, "test.json")
        with open(dataset_path, "w") as f:
            json.dump(sample_dataset, f)

        with patch("routes.datasets.UPLOAD_DIR", temp_upload_dir):
            response = client.delete("/api/datasets/test.json")

            assert response.status_code == 200
            assert not os.path.exists(dataset_path)

    def test_delete_nonexistent_dataset(self, client, temp_upload_dir):
        """Test deleting nonexistent dataset."""
        with patch("routes.datasets.UPLOAD_DIR", temp_upload_dir):
            response = client.delete("/api/datasets/nonexistent.json")

            assert response.status_code == 404
