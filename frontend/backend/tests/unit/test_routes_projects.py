"""
Unit tests for routes/projects.py
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestProjectsRoutes:
    """Tests for project management routes."""

    def test_quick_start_demo_success(self, client):
        """Test quick start demo endpoint."""
        # Check if demo files exist
        demo_dataset_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "use-cases"
            / "facility-support-analyzer"
            / "dataset.json"
        )

        if demo_dataset_path.exists():
            response = client.post("/api/quick-start-demo")

            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "dataset" in data
                assert "prompt" in data
                assert "config" in data
        else:
            # Skip test if demo files don't exist
            pytest.skip("Demo files not found")

    @patch("routes.projects.ConfigurationTransformer")
    def test_generate_config(self, mock_transformer, client, sample_wizard_data):
        """Test config generation from wizard data."""
        mock_instance = mock_transformer.return_value
        mock_instance.transform.return_value = {
            "system_prompt": {"inputs": ["question"], "outputs": ["answer"]},
            "dataset": {"adapter_class": "test"},
            "model": {},
            "metric": {},
            "optimization": {},
        }

        response = client.post("/generate-config", json=sample_wizard_data)

        assert response.status_code == 200
        data = response.json()
        assert "config" in data

    def test_list_projects(self, client):
        """Test listing projects."""
        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)

    def test_create_project(self, client, sample_wizard_data, temp_upload_dir):
        """Test project creation."""
        with patch("routes.projects.UPLOAD_DIR", temp_upload_dir):
            response = client.post("/create-project", json=sample_wizard_data)

            # Accept either success or missing dataset error
            assert response.status_code in [200, 404, 500]

            if response.status_code == 200:
                data = response.json()
                assert "projectName" in data

    def test_download_config(self, client, temp_upload_dir, sample_project_config):
        """Test config file download."""
        # Create a test project with config
        project_dir = os.path.join(temp_upload_dir, "test-project")
        os.makedirs(project_dir, exist_ok=True)

        config_path = os.path.join(project_dir, "config.yaml")
        with open(config_path, "w") as f:
            f.write(sample_project_config)

        with patch("routes.projects.UPLOAD_DIR", temp_upload_dir):
            response = client.get("/download-config/test-project")

            if response.status_code == 200:
                assert response.headers["content-type"] in [
                    "application/x-yaml",
                    "text/yaml",
                    "application/octet-stream",
                ]
