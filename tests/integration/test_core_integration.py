import json
import os
import pytest
from pathlib import Path

# Import unittest.mock which should always be available
from unittest.mock import patch, MagicMock

# Check if core components are available
CORE_COMPONENTS_AVAILABLE = False
try:
    from llama_prompt_ops.core.datasets import ConfigurableJSONAdapter
    from llama_prompt_ops.core.metrics import FacilityMetric
    from llama_prompt_ops.core.model import ModelAdapter
    from llama_prompt_ops.core.prompt_strategies import BasicOptimizationStrategy
    from llama_prompt_ops.core.migrator import PromptMigrator

    CORE_COMPONENTS_AVAILABLE = True
except ImportError as e:
    # Record the specific import error for diagnostics
    CORE_IMPORT_ERROR = str(e)


# Define a function to get the skip reason
def get_core_skip_reason():
    if not CORE_COMPONENTS_AVAILABLE:
        return f"Core components not available: {CORE_IMPORT_ERROR if 'CORE_IMPORT_ERROR' in globals() else 'Unknown import error'}"
    return None


class MockModelAdapter:
    """Mock model adapter for testing without actual API calls."""

    def __init__(self, *args, **kwargs):
        self.model_name = kwargs.get("model_name", "mock-model")
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 1000)

    def generate(self, prompt, *args, **kwargs):
        """Mock generation that returns a predefined response."""
        # Return a valid JSON response for facility categorization
        return json.dumps(
            {
                "categories": {
                    "routine_maintenance_requests": True,
                    "customer_feedback_and_complaints": False,
                    "specialized_cleaning_services": False,
                    "emergency_repair_services": False,
                },
                "sentiment": "neutral",
                "urgency": "medium",
            }
        )


@pytest.mark.skipif(
    not CORE_COMPONENTS_AVAILABLE,
    reason=get_core_skip_reason() or "Core components available",
)
def test_dataset_adapter_loading(facility_dataset_path):
    """Test that the dataset adapter can load the facility dataset."""
    adapter = ConfigurableJSONAdapter(
        dataset_path=facility_dataset_path,
        input_field=["fields", "input"],
        golden_output_field="answer",
    )

    data = adapter.load_raw_data()
    assert len(data) > 0
    assert "fields" in data[0]
    assert "input" in data[0]["fields"]
    assert "answer" in data[0]


@pytest.mark.skipif(
    not CORE_COMPONENTS_AVAILABLE,
    reason=get_core_skip_reason() or "Core components available",
)
def test_dataset_to_model_flow(sample_facility_data):
    """Test the flow from dataset loading to model inference with mocks."""
    # Create a temporary dataset file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        json.dump(sample_facility_data, tmp)
        tmp_path = tmp.name

    try:
        # Set up the adapter
        adapter = ConfigurableJSONAdapter(
            dataset_path=tmp_path,
            input_field=["fields", "input"],
            golden_output_field="answer",
        )

        # Load and adapt the data
        standardized_data = adapter.adapt()
        assert len(standardized_data) > 0
        assert "inputs" in standardized_data[0]
        assert "outputs" in standardized_data[0]

        # Set up mock model
        model = MockModelAdapter(model_name="mock-llm")

        # Generate a response
        example = standardized_data[0]
        prompt = f"Analyze this customer message and categorize it:\n\n{example['inputs']['question']}"
        response = model.generate(prompt)

        # Verify response format
        result = json.loads(response)
        assert "categories" in result
        assert "sentiment" in result
        assert "urgency" in result
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@pytest.mark.skipif(
    not CORE_COMPONENTS_AVAILABLE,
    reason=get_core_skip_reason() or "Core components available",
)
def test_metric_evaluation():
    """Test that the metric can evaluate predictions against ground truth."""
    # Create a metric instance
    metric = FacilityMetric()

    # Create test data
    gold = {
        "categories": {
            "routine_maintenance_requests": True,
            "customer_feedback_and_complaints": False,
            "specialized_cleaning_services": False,
            "emergency_repair_services": False,
        },
        "sentiment": "neutral",
        "urgency": "medium",
    }

    # Test with exact match
    pred = gold.copy()
    gold_str = json.dumps(gold)
    pred_str = json.dumps(pred)

    # Pass trace=True to get a dictionary result instead of a float
    result = metric(gold_str, pred_str, trace=True)

    # Check results
    assert result["correct_categories"] == 1.0
    assert result["correct_sentiment"] is True
    assert result["correct_urgency"] is True
    assert result["total"] > 0

    # Test with partial match
    pred["categories"]["routine_maintenance_requests"] = False
    pred["categories"]["emergency_repair_services"] = True
    pred["urgency"] = "high"
    pred_str = json.dumps(pred)

    # Pass trace=True to get a dictionary result instead of a float
    result = metric(gold_str, pred_str, trace=True)

    # Check results
    assert result["correct_categories"] < 1.0
    assert result["correct_sentiment"] is True
    assert result["correct_urgency"] is False
    assert result["total"] > 0


@pytest.mark.skipif(
    not CORE_COMPONENTS_AVAILABLE,
    reason=get_core_skip_reason() or "Core components available",
)
def test_strategy_execution():
    """Test execution of strategies with minimal components."""
    # Create mock components
    model = MockModelAdapter(model_name="mock-llm")
    metric = FacilityMetric()

    # Create a simple strategy
    strategy = BasicOptimizationStrategy(
        model_name="mock-llm",
        metric=metric,
        num_threads=1,  # Use minimal resources for testing
    )

    # Sample data
    example = {
        "inputs": {
            "question": "Subject: HVAC Maintenance Request\n\nDear Support Team,\n\nOur HVAC system needs routine maintenance. It's not urgent but should be addressed soon.\n\nThank you,\nCustomer"
        },
        "outputs": {
            "answer": json.dumps(
                {
                    "categories": {
                        "routine_maintenance_requests": True,
                        "customer_feedback_and_complaints": False,
                        "specialized_cleaning_services": False,
                        "emergency_repair_services": False,
                    },
                    "sentiment": "neutral",
                    "urgency": "medium",
                }
            )
        },
    }

    # Run optimization with minimal data
    initial_prompt = "Analyze this customer message and categorize it:"
    prompt_data = {
        "text": initial_prompt,
        "inputs": ["question"],
        "outputs": ["answer"],
        "examples": [example],
        "validation_examples": [example],
    }

    # Call the strategy's run method
    result = strategy.run(prompt_data)

    # Check that we get a result
    assert result is not None
    # In BasicOptimizationStrategy, the result is a string containing the optimized prompt
    assert isinstance(result, str)
    assert len(result) > 0
    # The result should contain the original prompt text
    assert initial_prompt in result or initial_prompt.strip() in result


@pytest.mark.skipif(
    not CORE_COMPONENTS_AVAILABLE,
    reason=get_core_skip_reason() or "Core components available",
)
def test_config_loading(facility_config_path):
    """Test loading configuration from YAML file."""
    import yaml

    # Load the config
    with open(facility_config_path, "r") as f:
        config = yaml.safe_load(f)

    # Verify key sections
    assert "dataset" in config
    assert "model" in config
    assert "metric" in config
    assert "optimization" in config

    # Check dataset config
    assert "path" in config["dataset"]
    assert "input_field" in config["dataset"]
    assert "golden_output_field" in config["dataset"]

    # Check model config
    assert "name" in config["model"]

    # Check metric config
    assert "class" in config["metric"]
    assert config["metric"]["class"] == "llama_prompt_ops.core.metrics.FacilityMetric"


@pytest.mark.skipif(
    not CORE_COMPONENTS_AVAILABLE,
    reason=get_core_skip_reason() or "Core components available",
)
def test_end_to_end_flow_with_mocks(facility_config_path):
    """Test the entire optimization process with simplified components."""
    import yaml

    # Load the config
    with open(facility_config_path, "r") as f:
        config = yaml.safe_load(f)

    # Create a mock model
    model = MockModelAdapter(model_name="mock-llm")

    # Create a simple strategy
    strategy = BasicOptimizationStrategy(
        model_name="mock-llm",
        metric=FacilityMetric(),
        num_threads=1,  # Use minimal resources for testing
    )

    # Create a mock DSPy program with the expected structure
    mock_program = MagicMock()
    mock_program.signature = MagicMock()
    mock_program.signature.instructions = "Optimized prompt"

    # Patch the ModelAdapter to use our mock
    with patch("llama_prompt_ops.core.model.ModelAdapter", MockModelAdapter):
        # Create a migrator with the strategy
        migrator = PromptMigrator(
            strategy=strategy, task_model=model, prompt_model=model
        )

        # Mock the strategy.run method to return our mock program
        with patch.object(strategy, "run", return_value=mock_program):
            # Create a simple prompt data dictionary
            prompt_data = {
                "text": "Analyze this customer message and categorize it:",
                "inputs": ["question"],
                "outputs": ["answer"],
            }

            # Run the optimization process
            result = migrator.optimize(prompt_data)

            # Check results
            assert result is not None
            assert result.signature.instructions == "Optimized prompt"
