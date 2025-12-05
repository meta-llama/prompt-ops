"""
Unit tests for summary utilities.

Tests the summary creation utility functions in isolation.
"""

from unittest.mock import MagicMock

import pytest

from prompt_ops.core.utils.summary_utils import (
    create_and_display_summary,
    create_pre_optimization_summary,
)
from prompt_ops.core.utils.telemetry import PreOptimizationSummary


class TestSummaryUtils:
    """Test cases for summary utility functions."""

    def test_create_pre_optimization_summary_basic(self):
        """Test basic summary creation with minimal strategy."""
        # Create a mock strategy with required attributes
        mock_strategy = MagicMock()
        mock_strategy.proposer_kwargs = None
        mock_strategy.compute_baseline = False
        mock_strategy._get_model_name.side_effect = lambda model: f"mock_{model}"
        mock_strategy.task_model = "task_model"
        mock_strategy.prompt_model = "prompt_model"
        mock_strategy.metric = MagicMock()
        mock_strategy.metric.__name__ = "test_metric"
        mock_strategy.trainset = [1, 2, 3]  # 3 items
        mock_strategy.valset = [1, 2]  # 2 items
        mock_strategy.auto = "basic"
        mock_strategy.max_labeled_demos = 5
        mock_strategy.max_bootstrapped_demos = 4
        mock_strategy.num_candidates = 10
        mock_strategy.num_threads = 18
        mock_strategy.init_temperature = 0.5
        mock_strategy.seed = 9

        prompt_data = {"text": "test prompt"}

        # Create summary
        summary = create_pre_optimization_summary(mock_strategy, prompt_data)

        # Verify summary
        assert isinstance(summary, PreOptimizationSummary)
        assert summary.task_model == "mock_task_model"
        assert summary.proposer_model == "mock_prompt_model"
        assert summary.metric_name == "test_metric"
        assert summary.train_size == 3
        assert summary.val_size == 2
        assert summary.guidance is None
        assert summary.baseline_score is None
        assert summary.mipro_params["auto_user"] == "basic"
        assert summary.mipro_params["auto_dspy"] == "light"

    def test_create_pre_optimization_summary_with_guidance(self):
        """Test summary creation with guidance/tips."""
        mock_strategy = MagicMock()
        mock_strategy.proposer_kwargs = {"tip": "Use clear instructions"}
        mock_strategy.compute_baseline = False
        mock_strategy._get_model_name.side_effect = lambda model: f"mock_{model}"
        mock_strategy.task_model = "task_model"
        mock_strategy.prompt_model = "prompt_model"
        mock_strategy.metric = MagicMock()
        mock_strategy.metric.__name__ = "test_metric"
        mock_strategy.trainset = []
        mock_strategy.valset = []
        mock_strategy.auto = "basic"

        # Set other required attributes with defaults
        for attr in [
            "max_labeled_demos",
            "max_bootstrapped_demos",
            "num_candidates",
            "num_threads",
            "init_temperature",
            "seed",
        ]:
            setattr(mock_strategy, attr, 1)

        prompt_data = {"text": "test prompt"}

        summary = create_pre_optimization_summary(mock_strategy, prompt_data)

        assert summary.guidance == "Use clear instructions"

    def test_create_pre_optimization_summary_with_baseline(self):
        """Test summary creation with baseline score computation."""
        mock_strategy = MagicMock()
        mock_strategy.proposer_kwargs = None
        mock_strategy.compute_baseline = True
        mock_strategy._compute_baseline_score.return_value = 0.75
        mock_strategy._get_model_name.side_effect = lambda model: f"mock_{model}"
        mock_strategy.task_model = "task_model"
        mock_strategy.prompt_model = "prompt_model"
        mock_strategy.metric = MagicMock()
        mock_strategy.metric.__name__ = "test_metric"
        mock_strategy.trainset = []
        mock_strategy.valset = []
        mock_strategy.auto = "basic"

        # Set other required attributes with defaults
        for attr in [
            "max_labeled_demos",
            "max_bootstrapped_demos",
            "num_candidates",
            "num_threads",
            "init_temperature",
            "seed",
        ]:
            setattr(mock_strategy, attr, 1)

        prompt_data = {"text": "test prompt"}

        summary = create_pre_optimization_summary(mock_strategy, prompt_data)

        assert summary.baseline_score == 0.75
        mock_strategy._compute_baseline_score.assert_called_once_with(prompt_data)

    def test_create_pre_optimization_summary_handles_missing_attributes(self):
        """Test that summary creation handles missing strategy attributes gracefully."""
        # Create minimal mock strategy
        mock_strategy = MagicMock()

        # Remove some attributes to test defaults
        del mock_strategy.proposer_kwargs
        del mock_strategy.compute_baseline
        del mock_strategy._get_model_name
        del mock_strategy.task_model
        del mock_strategy.prompt_model
        del mock_strategy.metric
        del mock_strategy.trainset
        del mock_strategy.valset

        prompt_data = {"text": "test prompt"}

        # Should not raise an exception
        summary = create_pre_optimization_summary(mock_strategy, prompt_data)

        # Should have safe defaults
        assert summary.task_model == "Unknown"
        assert summary.proposer_model == "Unknown"
        assert summary.metric_name == "None"
        assert summary.train_size == 0
        assert summary.val_size == 0
        assert summary.guidance is None
        assert summary.baseline_score is None

    def test_create_and_display_summary(self):
        """Test the convenience function that creates and displays summary."""
        mock_strategy = MagicMock()
        mock_strategy.proposer_kwargs = None
        mock_strategy.compute_baseline = False
        mock_strategy._get_model_name.side_effect = lambda model: f"mock_{model}"
        mock_strategy.task_model = "task_model"
        mock_strategy.prompt_model = "prompt_model"
        mock_strategy.metric = MagicMock()
        mock_strategy.metric.__name__ = "test_metric"
        mock_strategy.trainset = []
        mock_strategy.valset = []
        mock_strategy.auto = "basic"

        # Set other required attributes with defaults
        for attr in [
            "max_labeled_demos",
            "max_bootstrapped_demos",
            "num_candidates",
            "num_threads",
            "init_temperature",
            "seed",
        ]:
            setattr(mock_strategy, attr, 1)

        prompt_data = {"text": "test prompt"}

        summary = create_and_display_summary(mock_strategy, prompt_data)

        # Should return a summary
        assert isinstance(summary, PreOptimizationSummary)
        assert summary.task_model == "mock_task_model"
        assert summary.proposer_model == "mock_prompt_model"
        assert summary.metric_name == "test_metric"

    def test_create_and_display_summary_handles_errors(self):
        """Test that create_and_display_summary handles errors gracefully."""
        # Create a strategy that will cause an error
        mock_strategy = MagicMock()
        mock_strategy._get_model_name.side_effect = Exception("Test error")

        prompt_data = {"text": "test prompt"}

        summary = create_and_display_summary(mock_strategy, prompt_data)

        # Should return a minimal summary instead of failing
        assert isinstance(summary, PreOptimizationSummary)
        assert summary.task_model == "Unknown"
