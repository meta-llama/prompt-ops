import json
from pathlib import Path

import pytest


@pytest.fixture
def facility_dataset_path():
    """Fixture providing path to the facility dataset."""
    base_dir = Path(__file__).parent.parent.parent
    return str(
        base_dir / "use-cases" / "facility-support-analyzer" / "facility_v2_test.json"
    )


@pytest.fixture
def facility_config_path():
    """Fixture providing path to the facility config."""
    base_dir = Path(__file__).parent.parent.parent
    return str(
        base_dir / "use-cases" / "facility-support-analyzer" / "facility-simple.yaml"
    )


@pytest.fixture
def facility_prompt_path():
    """Fixture providing path to the facility system prompt."""
    base_dir = Path(__file__).parent.parent.parent
    return str(
        base_dir / "use-cases" / "facility-support-analyzer" / "facility_prompt_sys.txt"
    )


@pytest.fixture
def sample_facility_data(facility_dataset_path):
    """Fixture providing a small sample of facility data for testing."""
    with open(facility_dataset_path, "r") as f:
        data = json.load(f)
        # Return just the first 2 items for faster testing
        return data[:2]


@pytest.fixture
def mock_model_response():
    """Mock model response for testing."""
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
