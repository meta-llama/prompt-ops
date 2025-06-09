import json
import os
from pathlib import Path

# Import unittest.mock which should always be available
from unittest.mock import MagicMock, patch

import pytest

# Check if core components are available
CORE_COMPONENTS_AVAILABLE = False
try:
    from llama_prompt_ops.core.datasets import ConfigurableJSONAdapter
    from llama_prompt_ops.core.metrics import FacilityMetric
    from llama_prompt_ops.core.migrator import PromptMigrator
    from llama_prompt_ops.core.model import ModelAdapter
    from llama_prompt_ops.core.prompt_strategies import BasicOptimizationStrategy

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


@pytest.mark.skipif(
    not CORE_COMPONENTS_AVAILABLE,
    reason=get_core_skip_reason() or "Core components available",
)
def test_basic_optimization_strategy_num_threads_integration():
    """
    Integration test for the MIPROv2 num_threads bug fix.

    This test verifies that BasicOptimizationStrategy correctly passes num_threads
    to the dspy library without causing parameter errors. This is a regression test
    for the bug where num_threads was incorrectly passed to MIPROv2 constructor.
    """
    import json
    import tempfile

    # Create minimal test data
    test_data = [
        {
            "inputs": {"question": "Test maintenance request"},
            "outputs": {
                "answer": json.dumps(
                    {
                        "categories": {"routine_maintenance_requests": True},
                        "sentiment": "neutral",
                        "urgency": "low",
                    }
                )
            },
        },
        {
            "inputs": {"question": "Emergency repair needed"},
            "outputs": {
                "answer": json.dumps(
                    {
                        "categories": {"emergency_repair_services": True},
                        "sentiment": "urgent",
                        "urgency": "high",
                    }
                )
            },
        },
    ]

    # Create temporary dataset file
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        json.dump(test_data, tmp)
        tmp_path = tmp.name

    try:
        # Load dataset
        adapter = ConfigurableJSONAdapter(
            dataset_path=tmp_path,
            input_field=["inputs", "question"],
            golden_output_field=["outputs", "answer"],
        )

        dataset = adapter.adapt()

        # Create strategy with specific num_threads value to test the fix
        strategy = BasicOptimizationStrategy(
            num_threads=2,  # Specific value to verify correct parameter passing
            max_bootstrapped_demos=1,  # Minimal for faster testing
            max_labeled_demos=1,
            num_trials=1,  # Single trial for speed
            metric=FacilityMetric(),
        )

        # Set up datasets (minimal size for integration test)
        strategy.trainset = dataset[:1]  # Use just one example
        strategy.valset = dataset[1:2] if len(dataset) > 1 else dataset[:1]

        # Mock the models to avoid real API calls but test dspy integration
        with patch("dspy.LM") as mock_lm:
            # Configure mock to return valid responses
            mock_instance = MagicMock()
            mock_lm.return_value = mock_instance

            # The key test: verify that strategy instantiation and basic setup
            # works without TypeError from incorrect num_threads parameter passing
            strategy.task_model = mock_instance
            strategy.prompt_model = mock_instance

            prompt_data = {
                "text": "Categorize customer messages",
                "inputs": ["question"],
                "outputs": ["answer"],
            }

            # This is the critical test - the strategy should be able to configure
            # without throwing a TypeError about num_threads parameter
            try:
                # We patch the actual dspy.MIPROv2 to verify it's called correctly
                with (
                    patch("dspy.MIPROv2") as mock_mipro,
                    patch("dspy.ChainOfThought") as mock_cot,
                ):

                    mock_optimizer = MagicMock()
                    mock_mipro.return_value = mock_optimizer
                    mock_program = MagicMock()
                    mock_cot.return_value = mock_program
                    mock_optimizer.compile.return_value = mock_program

                    # This call should succeed without TypeError
                    result = strategy.run(prompt_data)

                    # Verify correct API usage:
                    # 1. num_threads should NOT be in MIPROv2 constructor
                    mock_mipro.assert_called_once()
                    constructor_kwargs = mock_mipro.call_args.kwargs
                    assert (
                        "num_threads" not in constructor_kwargs
                    ), "num_threads should not be passed to MIPROv2 constructor"

                    # 2. num_threads SHOULD be in compile eval_kwargs
                    mock_optimizer.compile.assert_called_once()
                    compile_kwargs = mock_optimizer.compile.call_args.kwargs
                    assert (
                        "eval_kwargs" in compile_kwargs
                    ), "eval_kwargs should be present in compile call"
                    assert (
                        compile_kwargs["eval_kwargs"]["num_threads"] == 2
                    ), "num_threads should be correctly passed via eval_kwargs"

                    # 3. Strategy should return a result
                    assert result is not None

                    print(
                        "✅ Integration test passed: num_threads correctly handled by dspy"
                    )

            except TypeError as e:
                if "num_threads" in str(e):
                    pytest.fail(
                        f"Bug regression detected: {e}. "
                        "The num_threads parameter is being incorrectly passed to MIPROv2 constructor."
                    )
                else:
                    # Re-raise other TypeErrors as they might be legitimate
                    raise

    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
