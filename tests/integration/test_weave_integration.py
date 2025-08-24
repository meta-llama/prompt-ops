"""
Integration tests for W&B Weave tracking functionality.

This test suite validates that the Weave integration correctly tracks:
1. Prompt versioned objects
2. Dataset versioned objects  
3. LLM call traces (via weave.init() automatic tracing)
"""
import os
import tempfile
import uuid
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

import pytest
import yaml
from datasets import Dataset

# Import our integration components
from llama_prompt_ops.integrations.weave_tracker import WeaveTracker


class TestWeaveIntegration:
    """
    Comprehensive test suite for Weave integration.
    
    Tests validate the three core requirements:
    1. Prompt versioning and tracking
    2. Dataset versioning and tracking
    3. Automatic LLM call tracing via weave.init()
    """

    @pytest.fixture
    def test_project_name(self) -> str:
        """Generate unique test project name to avoid conflicts."""
        return f"llama-prompt-ops-test-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def sample_dataset(self) -> Dataset:
        """Create a sample dataset for testing."""
        return Dataset.from_dict({
            "question": ["What is AI?", "Explain machine learning", "Define neural networks"],
            "answer": ["AI is artificial intelligence", "ML is a subset of AI", "Neural networks are computing systems"]
        })

    def test_weave_tracker_initialization(self, test_project_name: str):
        """Test that WeaveTracker initializes correctly and calls weave.init()."""
        with patch('llama_prompt_ops.integrations.weave_tracker.weave') as mock_weave:
            tracker = WeaveTracker(project_name=test_project_name, enabled=True)
            
            assert tracker.project_name == test_project_name
            assert tracker.enabled is True
            
            # Verify weave.init was called with correct project name
            mock_weave.init.assert_called_once_with(test_project_name)
        
        # Test disabled tracker
        disabled_tracker = WeaveTracker(project_name=test_project_name, enabled=False)
        assert disabled_tracker.enabled is False

    def test_prompt_versioning_with_string_prompt(self, test_project_name: str):
        """
        REQUIREMENT 1: Test prompt versioned objects using weave.StringPrompt.
        
        Validates that:
        - Original and optimized prompts are tracked using weave.StringPrompt
        - Same-named prompts create versions
        - weave.publish() is called correctly
        """
        with patch('llama_prompt_ops.integrations.weave_tracker.weave') as mock_weave, \
             patch('llama_prompt_ops.integrations.weave_tracker.StringPrompt') as mock_string_prompt_class:
            
            mock_weave.init.return_value = MagicMock()
            mock_weave.publish.return_value = "weave://test/project/StringPrompt/system_prompt:v1"
            
            tracker = WeaveTracker(project_name=test_project_name, enabled=True)
            
            original_prompt = "You are a helpful assistant."
            optimized_prompt = "You are a helpful AI assistant specialized in Llama models."
            
            # Track prompt evolution
            result = tracker.track_prompt_evolution(
                original_prompt=original_prompt,
                optimized_prompt=optimized_prompt,
                prompt_name="system_prompt"
            )
            
            assert result is not None
            
            # Verify StringPrompt objects were created correctly (no name in constructor)
            assert mock_string_prompt_class.call_count == 2
            mock_string_prompt_class.assert_any_call(original_prompt)
            mock_string_prompt_class.assert_any_call(optimized_prompt)
            
            # Verify weave.publish was called twice with same name for versioning
            assert mock_weave.publish.call_count == 2
            # Check that both calls used the same name parameter
            publish_calls = mock_weave.publish.call_args_list
            assert publish_calls[0][1]['name'] == "system_prompt"
            assert publish_calls[1][1]['name'] == "system_prompt"

    def test_dataset_versioning_with_weave_dataset(self, test_project_name: str, sample_dataset: Dataset):
        """
        REQUIREMENT 2: Test dataset versioned objects using weave.Dataset.
        
        Validates that:
        - Datasets are converted and tracked using weave.Dataset
        - Dataset names are set correctly for versioning
        - weave.publish() is called correctly
        """
        with patch('llama_prompt_ops.integrations.weave_tracker.weave') as mock_weave, \
             patch('llama_prompt_ops.integrations.weave_tracker.Dataset') as mock_dataset_class:
            
            mock_weave.init.return_value = MagicMock()
            mock_weave.publish.return_value = "weave://test/project/Dataset/dataset_train:v1"
            
            tracker = WeaveTracker(project_name=test_project_name, enabled=True)
            
            # Track dataset
            result = tracker.track_dataset(
                dataset=sample_dataset,
                split="train"
            )
            
            assert result is not None
            
            # Verify weave.Dataset was created with correct structure
            mock_dataset_class.assert_called_once()
            call_args = mock_dataset_class.call_args
            
            # Check the dataset was created with correct name and data
            assert call_args[1]["name"] == "dataset_train"
            assert len(call_args[1]["rows"]) == 3  # Our sample has 3 rows
            
            # Verify weave.publish was called
            mock_weave.publish.assert_called_once()

    def test_automatic_llm_tracing_via_weave_init(self, test_project_name: str):
        """
        REQUIREMENT 3: Test that weave.init() enables automatic LLM tracing.
        
        Validates that:
        - weave.init() is called during tracker initialization
        - This enables automatic tracing for supported LLM libraries
        - No additional wrapping is needed for basic LLM calls
        """
        with patch('llama_prompt_ops.integrations.weave_tracker.weave') as mock_weave:
            mock_client = MagicMock()
            mock_weave.init.return_value = mock_client
            
            # Initialize tracker
            tracker = WeaveTracker(project_name=test_project_name, enabled=True)
            
            # Verify weave.init was called (this enables automatic LLM tracing)
            mock_weave.init.assert_called_once_with(test_project_name)
            
            # Verify tracker recognizes it's enabled for automatic tracing
            assert tracker.is_enabled() is True
            
            # The automatic tracing happens via weave.init() - no additional setup needed
            # LLM calls made after this point will be automatically traced by Weave

    def test_weave_integration_can_be_disabled(self):
        """
        Test that Weave tracking can be completely disabled.
        
        This validates the requirement to choose whether to run with or without Weave.
        """
        # Test initialization with enabled=False
        tracker = WeaveTracker(project_name="test", enabled=False)
        assert not tracker.is_enabled()
        
        # Test that tracking operations return None when disabled
        result = tracker.track_prompt_evolution("original", "optimized")
        assert result is None
        
        sample_dataset = Dataset.from_dict({"test": ["data"]})
        result = tracker.track_dataset(sample_dataset)
        assert result is None

    def test_cli_integration_with_weave_config(self):
        """
        Test that CLI properly creates WeaveTracker from YAML config.
        """
        from llama_prompt_ops.interfaces.cli import create_weave_tracker_from_config
        
        # Test enabled configuration
        config_with_weave = {
            "weave": {
                "enabled": True,
                "project_name": "test-project",
                "entity": "test-entity"
            }
        }
        
        with patch('llama_prompt_ops.interfaces.cli.WeaveTracker') as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.is_enabled.return_value = True
            mock_tracker_class.return_value = mock_tracker
            
            result = create_weave_tracker_from_config(config_with_weave)
            
            assert result is not None
            mock_tracker_class.assert_called_once_with(
                project_name="test-project",
                entity="test-entity",
                enabled=True
            )
        
        # Test disabled configuration
        config_without_weave = {}
        result = create_weave_tracker_from_config(config_without_weave)
        assert result is None
        
        # Test explicitly disabled configuration
        config_disabled = {"weave": {"enabled": False}}
        result = create_weave_tracker_from_config(config_disabled)
        assert result is None

    def test_error_handling_when_weave_unavailable(self):
        """
        Test graceful degradation when Weave is unavailable.
        """
        with patch('llama_prompt_ops.integrations.weave_tracker.WEAVE_AVAILABLE', False):
            tracker = WeaveTracker(project_name="test", enabled=True)
            
            # Should disable tracking when weave is unavailable
            assert not tracker.is_enabled()
            
            # Operations should handle gracefully without crashing
            result = tracker.track_prompt_evolution("test", "optimized")
            assert result is None

    def test_weave_ref_retrieval_methods(self, test_project_name: str):
        """
        Test that get_prompt and get_dataset methods work with weave.ref().
        """
        with patch('llama_prompt_ops.integrations.weave_tracker.weave') as mock_weave:
            mock_weave.init.return_value = MagicMock()
            mock_ref = MagicMock()
            mock_ref.get.return_value = {"prompt": "test prompt"}
            mock_weave.ref.return_value = mock_ref
            
            tracker = WeaveTracker(project_name=test_project_name, enabled=True)
            
            # Test prompt retrieval
            result = tracker.get_prompt("system_prompt")
            mock_weave.ref.assert_called_with("system_prompt")
            mock_ref.get.assert_called()
            assert result == {"prompt": "test prompt"}
            
            # Test dataset retrieval
            mock_ref.get.return_value = {"dataset": "test data"}
            result = tracker.get_dataset("train")
            mock_weave.ref.assert_called_with("dataset_train")
            assert result == {"dataset": "test data"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])