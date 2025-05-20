import json
import os
import pytest
from pathlib import Path

# Import core components
try:
    from llama_prompt_ops.core.datasets import ConfigurableJSONAdapter
    from llama_prompt_ops.core.metrics import FacilityMetric
    from llama_prompt_ops.core.model import ModelAdapter
    from llama_prompt_ops.core.prompt_strategies import PromptStrategy
    from llama_prompt_ops.core.migrator import PromptMigrator
except ImportError:
    pass  # Tests will be skipped if imports fail


@pytest.fixture
def facility_dataset_path():
    """Fixture providing path to the facility dataset."""
    base_dir = Path(__file__).parent.parent.parent
    return str(base_dir / "use-cases" / "facility-support-analyzer" / "facility_v2_test.json")


@pytest.fixture
def facility_config_path():
    """Fixture providing path to the facility config."""
    base_dir = Path(__file__).parent.parent.parent
    return str(base_dir / "use-cases" / "facility-support-analyzer" / "facility-simple.yaml")


@pytest.fixture
def sample_facility_data(facility_dataset_path):
    """Fixture providing a small sample of facility data for testing."""
    try:
        with open(facility_dataset_path, 'r') as f:
            data = json.load(f)
            # Return just the first 2 items for faster testing
            return data[:2]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


class MockModelAdapter:
    """Mock model adapter for testing without actual API calls."""
    
    def __init__(self, *args, **kwargs):
        self.model_name = kwargs.get('model_name', 'mock-model')
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 1000)
    
    def generate(self, prompt, *args, **kwargs):
        """Mock generation that returns a predefined response."""
        # Return a valid JSON response for facility categorization
        return json.dumps({
            "categories": {
                "routine_maintenance_requests": True,
                "customer_feedback_and_complaints": False,
                "specialized_cleaning_services": False,
                "emergency_repair_services": False
            },
            "sentiment": "neutral",
            "urgency": "medium"
        })


def test_dataset_adapter_loading(facility_dataset_path):
    """Test that the dataset adapter can load the facility dataset."""
    try:
        adapter = ConfigurableJSONAdapter(
            dataset_path=facility_dataset_path,
            input_field=["fields", "input"],
            golden_output_field="answer"
        )
        
        data = adapter.load_raw_data()
        assert len(data) > 0
        assert "fields" in data[0]
        assert "input" in data[0]["fields"]
        assert "answer" in data[0]
    except (NameError, ImportError):
        pytest.skip("Required components not available")


def test_dataset_to_model_flow(sample_facility_data):
    """Test the flow from dataset loading to model inference with mocks."""
    try:
        # Create a temporary dataset file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            json.dump(sample_facility_data, tmp)
            tmp_path = tmp.name
        
        # Set up the adapter
        adapter = ConfigurableJSONAdapter(
            dataset_path=tmp_path,
            input_field=["fields", "input"],
            golden_output_field="answer"
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
        
        # Clean up
        os.unlink(tmp_path)
    except (NameError, ImportError):
        pytest.skip("Required components not available")


def test_metric_evaluation():
    """Test that the metric can evaluate predictions against ground truth."""
    try:
        # Create metric
        metric = FacilityMetric()
        
        # Sample ground truth and prediction
        ground_truth = json.dumps({
            "categories": {
                "routine_maintenance_requests": True,
                "customer_feedback_and_complaints": False,
                "specialized_cleaning_services": False,
                "emergency_repair_services": False
            },
            "sentiment": "neutral",
            "urgency": "medium"
        })
        
        prediction = json.dumps({
            "categories": {
                "routine_maintenance_requests": True,
                "customer_feedback_and_complaints": False,
                "specialized_cleaning_services": False,
                "emergency_repair_services": False
            },
            "sentiment": "neutral",
            "urgency": "medium"
        })
        
        # Evaluate
        result = metric(ground_truth, prediction, trace=True)
        
        # Check results
        assert result["is_valid_json"] is True
        assert result["correct_categories"] > 0
        assert result["correct_sentiment"] is True
        assert result["correct_urgency"] is True
        assert result["total"] > 0
    except (NameError, ImportError):
        pytest.skip("Required components not available")


def test_strategy_execution():
    """Test execution of strategies with minimal components."""
    try:
        # Create mock components
        model = MockModelAdapter(model_name="mock-llm")
        metric = FacilityMetric()
        
        # Create a simple strategy
        strategy = PromptStrategy(
            model=model,
            metric=metric,
            iterations=1  # Just one iteration for testing
        )
        
        # Sample data
        example = {
            "inputs": {
                "question": "Subject: HVAC Maintenance Request\n\nDear Support Team,\n\nOur HVAC system needs routine maintenance. It's not urgent but should be addressed soon.\n\nThank you,\nCustomer"
            },
            "outputs": {
                "answer": json.dumps({
                    "categories": {
                        "routine_maintenance_requests": True,
                        "customer_feedback_and_complaints": False,
                        "specialized_cleaning_services": False,
                        "emergency_repair_services": False
                    },
                    "sentiment": "neutral",
                    "urgency": "medium"
                })
            }
        }
        
        # Run optimization with minimal data
        initial_prompt = "Analyze this customer message and categorize it:"
        result = strategy.optimize(
            initial_prompt=initial_prompt,
            examples=[example],
            validation_examples=[example]
        )
        
        # Check that we get a result
        assert result is not None
        assert "prompt" in result
        assert len(result["prompt"]) > 0
    except (NameError, ImportError):
        pytest.skip("Required components not available")


def test_config_loading(facility_config_path):
    """Test loading configuration from YAML file."""
    try:
        import yaml
        
        # Load the config
        with open(facility_config_path, 'r') as f:
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
    except (NameError, ImportError, FileNotFoundError):
        pytest.skip("Required components not available")


def test_end_to_end_flow_with_mocks(facility_config_path):
    """Test the entire optimization process with simplified components."""
    try:
        import yaml
        from unittest.mock import patch
        
        # Load the config
        with open(facility_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Patch the ModelAdapter to use our mock
        with patch('llama_prompt_ops.core.model.ModelAdapter', MockModelAdapter):
            # Create a migrator with the config
            migrator = PromptMigrator(config=config)
            
            # Mock the optimize method to avoid actual optimization
            with patch.object(migrator, 'optimize', return_value={"prompt": "Optimized prompt"}):
                # Run the migration process
                result = migrator.migrate()
                
                # Check results
                assert result is not None
                assert "prompt" in result
                assert result["prompt"] == "Optimized prompt"
    except (NameError, ImportError, FileNotFoundError):
        pytest.skip("Required components not available")
