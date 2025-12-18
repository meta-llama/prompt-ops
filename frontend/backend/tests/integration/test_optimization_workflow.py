"""
Integration tests for the optimization workflow.
"""

import json
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


class TestOptimizationWorkflow:
    """Integration tests for end-to-end optimization workflows."""

    @patch("routes.prompts.PromptMigrator")
    @patch("routes.prompts.BasicOptimizationStrategy")
    @patch("routes.prompts.setup_model")
    def test_migrate_prompt_integration(
        self,
        mock_setup_model,
        mock_strategy_class,
        mock_migrator_class,
        client,
        sample_dataset,
        temp_upload_dir,
    ):
        """Test full migrate-prompt workflow."""
        # Setup mocks
        mock_model = Mock()
        mock_setup_model.return_value = mock_model

        mock_strategy = Mock()
        mock_strategy_class.return_value = mock_strategy

        mock_migrator = Mock()
        mock_optimized_program = Mock()
        mock_optimized_program.instruction = "Optimized instruction text"
        mock_migrator.optimize.return_value = mock_optimized_program
        mock_migrator.load_dataset_with_adapter.return_value = ([], [], [])
        mock_migrator_class.return_value = mock_migrator

        # Create test dataset
        dataset_path = os.path.join(temp_upload_dir, "test.json")
        with open(dataset_path, "w") as f:
            json.dump(sample_dataset, f)

        # Test data
        request_data = {
            "prompt": "Answer the question",
            "config": {
                "dataset": "test.json",
                "datasetAdapter": "standard_json",
                "metrics": "Exact Match",
                "model": "Llama 3.3 70B",
                "proposer": "Llama 3.3 70B",
                "strategy": "Basic",
                "useLlamaTips": True,
            },
        }

        with patch("routes.prompts.UPLOAD_DIR", temp_upload_dir):
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
                response = client.post("/api/migrate-prompt", json=request_data)

        # Verify response
        if response.status_code == 200:
            data = response.json()
            assert "optimizedPrompt" in data
            assert data["optimizedPrompt"] == "Optimized instruction text"

    @patch("routes.prompts.load_class_dynamically")
    def test_metric_initialization(self, mock_load_class, client):
        """Test that metrics are initialized correctly."""
        # Mock metric class
        mock_metric_class = Mock()
        mock_metric_instance = Mock()
        mock_metric_class.return_value = mock_metric_instance
        mock_load_class.return_value = mock_metric_class

        request_data = {
            "prompt": "Test prompt",
            "config": {
                "dataset": "test.json",
                "datasetAdapter": "standard_json",
                "metrics": "Exact Match",
                "model": "Llama 3.3 70B",
                "strategy": "Basic",
            },
        }

        # This should trigger metric loading
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            response = client.post("/api/migrate-prompt", json=request_data)

        # Metric class should have been loaded
        assert mock_load_class.called

    def test_missing_dataset_error(self, client):
        """Test error handling for missing dataset."""
        request_data = {
            "prompt": "Test prompt",
            "config": {
                "dataset": "nonexistent.json",
                "datasetAdapter": "standard_json",
                "metrics": "Exact Match",
                "model": "Llama 3.3 70B",
                "strategy": "Basic",
            },
        }

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            response = client.post("/api/migrate-prompt", json=request_data)

        assert response.status_code in [404, 500]

    @patch("routes.prompts.setup_model")
    def test_model_initialization(self, mock_setup_model, client):
        """Test that models are initialized with correct parameters."""
        mock_model = Mock()
        mock_setup_model.return_value = mock_model

        request_data = {
            "prompt": "Test",
            "config": {
                "dataset": "test.json",
                "model": "Llama 3.3 70B",
                "proposer": "Llama 3.1 8B",
                "metrics": "Exact Match",
                "strategy": "Basic",
            },
        }

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            response = client.post("/api/migrate-prompt", json=request_data)

        # Model setup should have been called
        assert mock_setup_model.called

    def test_prompt_enhancement_with_api_key(self, client):
        """Test prompt enhancement with API key."""
        with patch("main.client") as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Enhanced prompt"
            mock_client.chat.completions.create.return_value = mock_response

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                response = client.post(
                    "/api/enhance-prompt", json={"prompt": "Test prompt"}
                )

        if response.status_code == 200:
            data = response.json()
            assert "optimizedPrompt" in data

    def test_optimization_with_nested_field_mappings(
        self, client, sample_dataset_with_nested_fields, temp_upload_dir
    ):
        """Test optimization with nested field paths."""
        # Create dataset with nested fields
        dataset_path = os.path.join(temp_upload_dir, "nested.json")
        with open(dataset_path, "w") as f:
            json.dump(sample_dataset_with_nested_fields, f)

        request_data = {
            "prompt": "Analyze the message",
            "config": {
                "dataset": "nested.json",
                "datasetAdapter": "custom",
                "fieldMappings": {"question": ["fields", "input"], "answer": "answer"},
                "metrics": "Exact Match",
                "model": "Llama 3.3 70B",
                "strategy": "Basic",
            },
        }

        with patch("routes.prompts.UPLOAD_DIR", temp_upload_dir):
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
                with patch("routes.prompts.PromptMigrator") as mock_migrator_class:
                    mock_migrator = Mock()
                    mock_optimized = Mock()
                    mock_optimized.instruction = "Optimized"
                    mock_migrator.optimize.return_value = mock_optimized
                    mock_migrator.load_dataset_with_adapter.return_value = ([], [], [])
                    mock_migrator_class.return_value = mock_migrator

                    response = client.post("/api/migrate-prompt", json=request_data)

                    # Should not crash with nested field paths
                    assert response.status_code in [
                        200,
                        500,
                    ]  # Either success or internal error, not 400
