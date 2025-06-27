import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Check if optimization components are available
OPTIMIZATION_COMPONENTS_AVAILABLE = False
try:
    from llama_prompt_ops.core.datasets import ConfigurableJSONAdapter
    from llama_prompt_ops.core.metrics import FacilityMetric
    from llama_prompt_ops.core.model import ModelAdapter
    from llama_prompt_ops.core.model_strategies import LlamaStrategy

    OPTIMIZATION_COMPONENTS_AVAILABLE = True
except ImportError as e:
    # Record the specific import error for diagnostics
    OPTIMIZATION_IMPORT_ERROR = str(e)


# Define a function to get the skip reason
def get_optimization_skip_reason():
    if not OPTIMIZATION_COMPONENTS_AVAILABLE:
        return f"Optimization components not available: {OPTIMIZATION_IMPORT_ERROR if 'OPTIMIZATION_IMPORT_ERROR' in globals() else 'Unknown import error'}"
    return "Optimization components available"


@pytest.mark.skipif(
    not OPTIMIZATION_COMPONENTS_AVAILABLE, reason=get_optimization_skip_reason()
)
class TestOptimizationIntegration:
    """Integration tests for the optimization process."""

    def test_llama_strategy_run(self, facility_prompt_path, mock_model_response):
        """Test the LlamaStrategy run method from model_strategies."""
        # Read the system prompt
        with open(facility_prompt_path, "r") as f:
            system_prompt = f.read()

        # Create a mock model
        mock_model = MagicMock()
        mock_model.generate.return_value = mock_model_response

        # Create the strategy with the mock model
        strategy = LlamaStrategy(model=mock_model)

        # Mock the base_strategy.run method to return a dictionary
        mock_result = {"prompt": "Optimized prompt", "score": 0.9}
        strategy.base_strategy = MagicMock()
        strategy.base_strategy.run.return_value = mock_result

        # Prepare prompt data
        prompt_data = {
            "text": system_prompt,
            "inputs": ["message"],
            "outputs": ["categories"],
            "task_type": "classification",
        }

        # Test the run method
        result = strategy.run(prompt_data)

        # Check results
        assert result is not None
        assert isinstance(result, dict)
        assert result == mock_result

    def test_dataset_based_optimization(
        self, facility_dataset_path, mock_model_response
    ):
        """Test optimization using a dataset."""
        # Create adapter
        adapter = ConfigurableJSONAdapter(
            dataset_path=facility_dataset_path,
            input_field=["fields", "input"],
            golden_output_field="answer",
        )

        # Load a small sample
        adapter.load_raw_data()  # Load all data
        examples = adapter.adapt()  # Adapt loaded data

        # Create mock components
        mock_model = MagicMock()
        mock_model.generate.return_value = mock_model_response
        metric = FacilityMetric()

        # Create strategy with mocked base_strategy
        strategy = LlamaStrategy(model=mock_model, metric=metric)

        # Mock the base_strategy
        mock_result = {"prompt": "Optimized prompt", "score": 0.8}
        strategy.base_strategy = MagicMock()
        strategy.base_strategy.run.return_value = mock_result

        # Prepare prompt data
        prompt_data = {
            "text": "Analyze this customer message and categorize it:",
            "inputs": ["message"],
            "outputs": ["categories"],
            "task_type": "classification",
        }

        # Test the run method
        result = strategy.run(prompt_data)

        # Check results
        assert result is not None
        assert isinstance(result, dict)
        assert result == mock_result

    def test_end_to_end_optimization_flow(
        self, facility_dataset_path, mock_model_response
    ):
        """Test the complete optimization flow from dataset to optimized prompt."""
        # Create adapter
        adapter = ConfigurableJSONAdapter(
            dataset_path=facility_dataset_path,
            input_field=["fields", "input"],
            golden_output_field="answer",
        )

        # Load a small sample
        adapter.load_raw_data()  # Load all data
        examples = adapter.adapt()  # Adapt loaded data

        # Create mock model
        mock_model = MagicMock()
        mock_model.generate.return_value = mock_model_response

        # Create metric
        metric = FacilityMetric()

        # Create strategy with mocked base_strategy
        strategy = LlamaStrategy(model=mock_model, metric=metric)

        # Mock the base_strategy
        mock_result = {"prompt": "Optimized prompt for end-to-end test", "score": 0.9}
        strategy.base_strategy = MagicMock()
        strategy.base_strategy.run.return_value = mock_result

        # Prepare prompt data
        prompt_data = {
            "text": "Analyze this customer message and categorize it:",
            "inputs": ["message"],
            "outputs": ["categories"],
            "task_type": "classification",
        }

        # Test the run method
        result = strategy.run(prompt_data)

        # Check results
        assert result is not None
        assert isinstance(result, dict)
        assert "prompt" in result
        assert "score" in result
        assert result["score"] == 0.9

        # Test saving the prompt to a simple file
        import tempfile

        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".txt", delete=False
        ) as tmp_file:
            tmp_path = tmp_file.name
            # Write the prompt directly to the file
            tmp_file.write(result["prompt"])

        # Verify the saved file
        with open(tmp_path, "r") as f:
            saved_content = f.read()
            assert saved_content == result["prompt"]

        # Clean up
        os.unlink(tmp_path)

    def test_pre_optimization_summary_display(self, capsys):
        """Test that pre-optimization summary is displayed during optimization."""
        from llama_prompt_ops.core.prompt_strategies import BasicOptimizationStrategy
        from llama_prompt_ops.core.utils.telemetry import PreOptimizationSummary

        # Create a mock metric
        mock_metric = MagicMock()
        mock_metric.__name__ = "test_metric"

        # Create mock models
        mock_task_model = MagicMock()
        mock_task_model.model_name = "test_task_model"
        mock_prompt_model = MagicMock()
        mock_prompt_model.model_name = "test_prompt_model"

        # Create mock training and validation sets
        mock_trainset = [MagicMock() for _ in range(10)]
        mock_valset = [MagicMock() for _ in range(5)]

        # Create strategy
        strategy = BasicOptimizationStrategy(
            model_name="test_model",
            metric=mock_metric,
            task_model=mock_task_model,
            prompt_model=mock_prompt_model,
            trainset=mock_trainset,
            valset=mock_valset,
            auto="basic",
            max_labeled_demos=3,
            max_bootstrapped_demos=2,
            num_candidates=5,
            num_threads=4,
            init_temperature=0.7,
            seed=42,
        )

        # Mock the DSPy components to avoid actual optimization
        with (
            patch("dspy.Predict") as mock_predict,
            patch("dspy.MIPROv2") as mock_mipro,
            patch("dspy.Evaluate") as mock_evaluate,
        ):

            # Mock the baseline evaluation
            mock_evaluator = MagicMock()
            mock_evaluator.return_value = 0.65
            mock_evaluate.return_value = mock_evaluator

            # Mock the optimizer
            mock_optimizer = MagicMock()
            mock_optimizer.compile.return_value = MagicMock()
            mock_mipro.return_value = mock_optimizer

            # Prepare prompt data
            prompt_data = {
                "text": "Test prompt for optimization",
                "inputs": ["question"],
                "outputs": ["answer"],
            }

            # Run the strategy (this should display the summary)
            try:
                result = strategy.run(prompt_data)
            except Exception:
                # We expect this to fail due to mocking, but we want to check the logs
                pass

            # Capture the output
            captured = capsys.readouterr()

            # Check that the pre-optimization summary was displayed (it goes to stderr via logging)
            assert "=== Pre-Optimization Summary ===" in captured.err
            assert "test_task_model" in captured.err
            assert "test_prompt_model" in captured.err
            assert "test_metric" in captured.err
            assert "10 / 5" in captured.err  # train/val sizes
            assert '"auto_user":"basic"' in captured.err
            assert '"auto_dspy":"light"' in captured.err
            # Note: baseline score computation is currently disabled for performance
            # assert "0.6500" in captured.err  # baseline score
