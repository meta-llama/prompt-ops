# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Unit tests for the pre-optimization summary functionality.
"""

import json
from unittest.mock import Mock, patch

import pytest

from llama_prompt_ops.core.utils.telemetry import PreOptimizationSummary


class TestPreOptimizationSummary:
    """Test cases for PreOptimizationSummary class."""

    def test_to_pretty_basic(self):
        """Test basic pretty formatting without optional fields."""
        summary = PreOptimizationSummary(
            task_model="openai/gpt-4o-mini",
            proposer_model="openai/gpt-4o",
            metric_name="test_metric",
            train_size=100,
            val_size=20,
            mipro_params={
                "auto_user": "basic",
                "auto_dspy": "light",
                "max_labeled_demos": 5,
                "max_bootstrapped_demos": 4,
            },
        )

        result = summary.to_pretty()

        # Check that all required fields are present
        assert "=== Pre-Optimization Summary ===" in result
        assert "Task Model       : openai/gpt-4o-mini" in result
        assert "Proposer Model   : openai/gpt-4o" in result
        assert "Metric           : test_metric" in result
        assert "Train / Val size : 100 / 20" in result
        assert '"auto_user":"basic"' in result
        assert '"auto_dspy":"light"' in result

    def test_to_pretty_with_guidance(self):
        """Test pretty formatting with guidance field."""
        summary = PreOptimizationSummary(
            task_model="test_model",
            proposer_model="test_proposer",
            metric_name="test_metric",
            train_size=50,
            val_size=10,
            mipro_params={"test": "value"},
            guidance="Use chain-of-thought reasoning and show your work step by step",
        )

        result = summary.to_pretty()

        assert (
            "Guidance         : Use chain-of-thought reasoning and show your work step by step"
            in result
        )

    def test_to_pretty_with_long_guidance(self):
        """Test that long guidance is truncated properly."""
        long_guidance = "A" * 150  # 150 characters, should be truncated to 120 + "..."

        summary = PreOptimizationSummary(
            task_model="test_model",
            proposer_model="test_proposer",
            metric_name="test_metric",
            train_size=50,
            val_size=10,
            mipro_params={"test": "value"},
            guidance=long_guidance,
        )

        result = summary.to_pretty()

        # Should be truncated to 120 chars + "..."
        expected_guidance = "A" * 120 + "..."
        assert f"Guidance         : {expected_guidance}" in result

    def test_to_pretty_with_baseline_score(self):
        """Test pretty formatting with baseline score."""
        summary = PreOptimizationSummary(
            task_model="test_model",
            proposer_model="test_proposer",
            metric_name="test_metric",
            train_size=50,
            val_size=10,
            mipro_params={"test": "value"},
            baseline_score=0.7542,
        )

        result = summary.to_pretty()

        assert "Baseline score   : 0.7542" in result

    def test_to_json(self):
        """Test JSON serialization."""
        summary = PreOptimizationSummary(
            task_model="test_model",
            proposer_model="test_proposer",
            metric_name="test_metric",
            train_size=50,
            val_size=10,
            mipro_params={"auto_user": "basic", "num_threads": 8},
            guidance="test guidance",
            baseline_score=0.85,
        )

        result = summary.to_json()
        parsed = json.loads(result)

        assert parsed["task_model"] == "test_model"
        assert parsed["proposer_model"] == "test_proposer"
        assert parsed["metric_name"] == "test_metric"
        assert parsed["train_size"] == 50
        assert parsed["val_size"] == 10
        assert parsed["mipro_params"]["auto_user"] == "basic"
        assert parsed["mipro_params"]["num_threads"] == 8
        assert parsed["guidance"] == "test guidance"
        assert parsed["baseline_score"] == 0.85

    @patch("llama_prompt_ops.core.utils.telemetry.get_logger")
    def test_log(self, mock_get_logger):
        """Test that log() calls the logger with formatted output."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        summary = PreOptimizationSummary(
            task_model="test_model",
            proposer_model="test_proposer",
            metric_name="test_metric",
            train_size=50,
            val_size=10,
            mipro_params={"test": "value"},
        )

        summary.log()

        # Verify that get_logger was called
        mock_get_logger.assert_called_once()

        # Verify that progress was called with the formatted summary
        mock_logger.progress.assert_called_once()
        call_args = mock_logger.progress.call_args[0][0]
        assert "=== Pre-Optimization Summary ===" in call_args
        assert "test_model" in call_args

    def test_mipro_params_json_formatting(self):
        """Test that MIPRO params are properly JSON formatted in pretty output."""
        complex_params = {
            "auto_user": "intermediate",
            "auto_dspy": "medium",
            "max_labeled_demos": 10,
            "max_bootstrapped_demos": 8,
            "num_candidates": 15,
            "num_threads": 24,
            "init_temperature": 0.7,
            "seed": 42,
        }

        summary = PreOptimizationSummary(
            task_model="test_model",
            proposer_model="test_proposer",
            metric_name="test_metric",
            train_size=100,
            val_size=25,
            mipro_params=complex_params,
        )

        result = summary.to_pretty()

        # Check that the JSON is properly formatted (compact, no spaces)
        assert '"auto_user":"intermediate"' in result
        assert '"max_labeled_demos":10' in result
        assert '"init_temperature":0.7' in result

    def test_none_values_handling(self):
        """Test handling of None values for optional fields."""
        summary = PreOptimizationSummary(
            task_model="test_model",
            proposer_model="test_proposer",
            metric_name="test_metric",
            train_size=50,
            val_size=10,
            mipro_params={"test": "value"},
            guidance=None,
            baseline_score=None,
        )

        result = summary.to_pretty()

        # Should not contain guidance or baseline score lines
        assert "Guidance" not in result
        assert "Baseline score" not in result

        # But should contain all required fields
        assert "Task Model" in result
        assert "Proposer Model" in result
        assert "Metric" in result
