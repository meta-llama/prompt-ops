import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import core components
try:
    from llama_prompt_ops.core.datasets import ConfigurableJSONAdapter
    from llama_prompt_ops.core.metrics import FacilityMetric
    from llama_prompt_ops.core.model import ModelAdapter
    from llama_prompt_ops.core.prompt_strategies import LlamaStrategy
    from llama_prompt_ops.core.optimize import PromptOptimizer
except ImportError:
    pass  # Tests will be skipped if imports fail


# Fixtures are now defined in conftest.py


class TestOptimizationIntegration:
    """Integration tests for the optimization process."""

    def test_llama_strategy_fast_optimization(self, facility_prompt_path):
        """Test the LlamaStrategy fast optimization approach."""
        try:
            # Read the system prompt
            with open(facility_prompt_path, 'r') as f:
                system_prompt = f.read()
            
            # Create a mock model
            mock_model = MagicMock()
            mock_model.generate.return_value = "Optimized prompt template"
            
            # Create the strategy with the mock model
            strategy = LlamaStrategy(model=mock_model)
            
            # Test fast optimization
            result = strategy.optimize_fast(
                initial_prompt=system_prompt,
                task_type="classification",
                input_field="message",
                output_field="categories"
            )
            
            # Check results
            assert result is not None
            assert isinstance(result, dict)
            assert "prompt" in result
            assert len(result["prompt"]) > 0
        except (NameError, ImportError, FileNotFoundError):
            pytest.skip("Required components not available")

    def test_prompt_optimizer_with_mocks(self, mock_model_response):
        """Test the standalone PromptOptimizer with mocks."""
        try:
            # Create a mock model
            mock_model = MagicMock()
            mock_model.generate.return_value = mock_model_response
            
            # Create the optimizer with the mock model
            optimizer = PromptOptimizer(model=mock_model)
            
            # Test optimization
            initial_prompt = "Analyze this customer message and categorize it:"
            result = optimizer.optimize(
                prompt=initial_prompt,
                task_type="classification",
                use_inference=False  # Template-based optimization
            )
            
            # Check results
            assert result is not None
            assert isinstance(result, dict)
            assert "prompt" in result
            assert len(result["prompt"]) > 0
            
            # Test with inference-based optimization
            result_with_inference = optimizer.optimize(
                prompt=initial_prompt,
                task_type="classification",
                use_inference=True
            )
            
            # Check results
            assert result_with_inference is not None
            assert isinstance(result_with_inference, dict)
            assert "prompt" in result_with_inference
            assert len(result_with_inference["prompt"]) > 0
        except (NameError, ImportError):
            pytest.skip("Required components not available")

    def test_dataset_based_optimization(self, facility_dataset_path, mock_model_response):
        """Test optimization using a dataset."""
        try:
            # Create adapter
            adapter = ConfigurableJSONAdapter(
                dataset_path=facility_dataset_path,
                input_field=["fields", "input"],
                golden_output_field="answer"
            )
            
            # Load a small sample
            adapter.load_raw_data()  # Load all data
            examples = adapter.adapt()  # Adapt loaded data
            
            # Create mock components
            mock_model = MagicMock()
            mock_model.generate.return_value = mock_model_response
            metric = FacilityMetric()
            
            # Create strategy
            strategy = LlamaStrategy(
                model=mock_model,
                metric=metric,
                iterations=1  # Just one iteration for testing
            )
            
            # Run optimization
            initial_prompt = "Analyze this customer message and categorize it:"
            with patch.object(strategy, '_evaluate_prompt', return_value=0.8):
                result = strategy.optimize(
                    initial_prompt=initial_prompt,
                    examples=examples,
                    validation_examples=examples
                )
            
            # Check results
            assert result is not None
            assert "prompt" in result
            assert "score" in result
            assert result["score"] == 0.8
        except (NameError, ImportError, FileNotFoundError):
            pytest.skip("Required components not available")

    def test_end_to_end_optimization_flow(self, facility_dataset_path, mock_model_response):
        """Test the complete optimization flow from dataset to optimized prompt."""
        try:
            # Create adapter
            adapter = ConfigurableJSONAdapter(
                dataset_path=facility_dataset_path,
                input_field=["fields", "input"],
                golden_output_field="answer"
            )
            
            # Load a small sample
            adapter.load_raw_data()  # Load all data
            examples = adapter.adapt()  # Adapt loaded data
            
            # Create mock model
            mock_model = MagicMock()
            mock_model.generate.return_value = mock_model_response
            
            # Create metric
            metric = FacilityMetric()
            
            # Create strategy with mocked components
            strategy = LlamaStrategy(
                model=mock_model,
                metric=metric,
                iterations=1
            )
            
            # Mock internal methods to avoid actual optimization
            with patch.object(strategy, '_generate_candidates', return_value=["Candidate prompt 1"]):
                with patch.object(strategy, '_evaluate_prompt', return_value=0.9):
                    # Run optimization
                    initial_prompt = "Analyze this customer message and categorize it:"
                    result = strategy.optimize(
                        initial_prompt=initial_prompt,
                        examples=examples,
                        validation_examples=examples
                    )
            
            # Check results
            assert result is not None
            assert "prompt" in result
            assert "score" in result
            assert result["score"] == 0.9
            
            # Test saving the optimized prompt
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Save the optimized prompt
            from llama_prompt_ops.core.utils.format_utils import json_to_yaml_file
            json_to_yaml_file({"prompt": result["prompt"]}, tmp_path)
            
            # Verify the saved file
            import yaml
            with open(tmp_path, 'r') as f:
                saved_data = yaml.safe_load(f)
                assert "prompt" in saved_data
                assert saved_data["prompt"] == result["prompt"]
            
            # Clean up
            os.unlink(tmp_path)
        except (NameError, ImportError, FileNotFoundError):
            pytest.skip("Required components not available")
