"""
Unit tests for config_transformer.py
"""

import pytest
from config_transformer import ConfigurationTransformer


class TestConfigurationTransformer:
    """Tests for ConfigurationTransformer class."""

    def test_transform_basic_qa_config(self, sample_wizard_data):
        """Test transforming basic QA configuration."""
        transformer = ConfigurationTransformer()
        result = transformer.transform(sample_wizard_data, "test-project")

        assert "system_prompt" in result
        assert "dataset" in result
        assert "model" in result
        assert "metric" in result
        assert "optimization" in result

    def test_dataset_adapter_mapping_qa(self):
        """Test QA dataset adapter mapping."""
        wizard_data = {
            "dataset": "test.json",
            "datasetType": "qa",
            "fieldMappings": {"question": "q", "answer": "a"},
            "prompt": "Test prompt",
            "model": "Llama 3.3 70B",
            "metric": "Exact Match",
            "strategy": "Basic",
        }

        transformer = ConfigurationTransformer()
        result = transformer.transform(wizard_data, "test")

        assert (
            result["dataset"]["adapter_class"]
            == "prompt_ops.core.datasets.ConfigurableJSONAdapter"
        )
        assert "input_field" in result["dataset"]
        assert "golden_output_field" in result["dataset"]

    def test_rag_adapter_configuration(self):
        """Test RAG dataset adapter configuration."""
        wizard_data = {
            "dataset": "test.json",
            "datasetType": "rag",
            "fieldMappings": {"query": "question", "context": "ctx", "answer": "ans"},
            "prompt": "Test prompt",
            "model": "Llama 3.3 70B",
            "metric": "Semantic Similarity",
            "strategy": "Basic",
        }

        transformer = ConfigurationTransformer()
        result = transformer.transform(wizard_data, "test")

        assert (
            result["dataset"]["adapter_class"]
            == "prompt_ops.core.datasets.RAGJSONAdapter"
        )
        assert "question_field" in result["dataset"]
        assert "context_field" in result["dataset"]
        assert "golden_answer_field" in result["dataset"]

    def test_metric_mapping(self):
        """Test metric class mapping from wizard data."""
        wizard_data = {
            "dataset": "test.json",
            "datasetType": "qa",
            "fieldMappings": {"question": "q", "answer": "a"},
            "prompt": "Test",
            "model": "Llama 3.3 70B",
            "metric": "Exact Match",
            "strategy": "Basic",
        }

        transformer = ConfigurationTransformer()
        result = transformer.transform(wizard_data, "test")

        assert result["metric"]["class"] == "prompt_ops.core.metrics.ExactMatchMetric"

    def test_nested_field_mappings(self):
        """Test nested field path support."""
        wizard_data = {
            "dataset": "test.json",
            "datasetType": "custom",
            "fieldMappings": {"question": ["fields", "input"], "answer": "answer"},
            "prompt": "Test",
            "model": "Llama 3.3 70B",
            "metric": "Exact Match",
            "strategy": "Basic",
        }

        transformer = ConfigurationTransformer()
        result = transformer.transform(wizard_data, "test")

        assert result["dataset"]["input_field"] == ["fields", "input"]
