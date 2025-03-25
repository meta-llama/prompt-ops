"""
Tests for the prompt migrator core functionality.

This module contains unit tests for the PromptMigrator class and strategies.
"""

import pytest

from prompt_ops.core.migrator import PromptMigrator
from prompt_ops.core.prompt_strategies import BaseStrategy, LightOptimizationStrategy
from prompt_ops.core.metrics import ExactMatchMetric, json_evaluation_metric


def test_base_strategy():
    """Test that the base strategy returns the original prompt unchanged."""
    migrator = PromptMigrator(strategy=BaseStrategy())
    prompt = "This is a test prompt"
    result = migrator.optimize({"text": prompt})
    assert result == prompt


def test_light_strategy():
    """Test that the light strategy modifies the prompt as expected."""
    migrator = PromptMigrator(strategy=LightOptimizationStrategy(model_name="test-model"))
    prompt = "This is a test prompt"
    result = migrator.optimize({"text": prompt})
    assert "[Optimized for test-model]" in result
    assert prompt in result


def test_missing_text_key():
    """Test that an error is raised when the text key is missing."""
    migrator = PromptMigrator()
    with pytest.raises(ValueError):
        migrator.optimize({})


def test_metrics_evaluation():
    """Test that metrics evaluation works as expected."""
    # Create a migrator with metrics
    exact_match = ExactMatchMetric(case_sensitive=False)
    migrator = PromptMigrator(
        strategy=BaseStrategy(),
        metrics=[exact_match, json_evaluation_metric]
    )
    
    # Test exact match metric
    gold = "test"
    pred = "TEST"
    result = migrator.evaluate(gold, pred)
    assert "ExactMatchMetric_exact_match" in result
    assert result["ExactMatchMetric_exact_match"] == 1.0
    
    # Test with non-matching values
    gold = "test"
    pred = "different"
    result = migrator.evaluate(gold, pred)
    assert "ExactMatchMetric_exact_match" in result
    assert result["ExactMatchMetric_exact_match"] == 0.0
    
    # Test JSON evaluation
    gold = '{"name": "John", "age": 30}'
    pred = '{"name": "John", "age": 30}'
    result = migrator.evaluate(gold, pred)
    assert "json_evaluation_metric_json_precision" in result
    assert "json_evaluation_metric_json_recall" in result
    assert "json_evaluation_metric_json_f1" in result
    assert result["json_evaluation_metric_json_precision"] == 1.0
    assert result["json_evaluation_metric_json_recall"] == 1.0
    assert result["json_evaluation_metric_json_f1"] == 1.0
