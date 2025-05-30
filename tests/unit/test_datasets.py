import json
import os
import tempfile
import pytest
from unittest.mock import MagicMock

from llama_prompt_ops.core.datasets import (
    DatasetAdapter,
    ConfigurableJSONAdapter,
    load_dataset
)


@pytest.fixture
def simple_data_file():
    # Create a temporary JSON file for testing
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    test_data = [
        {"question": "Test question 1", "answer": "Test answer 1"},
        {"question": "Test question 2", "answer": "Test answer 2"},
    ]
    with open(temp_file.name, "w") as f:
        json.dump(test_data, f)
    
    yield temp_file, test_data
    
    # Clean up the temporary file
    os.unlink(temp_file.name)


@pytest.fixture
def nested_data_file():
    # Create a temporary JSON file with nested fields
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    nested_data = [
        {"fields": {"input": "Nested question 1"}, "output": {"text": "Nested answer 1"}},
        {"fields": {"input": "Nested question 2"}, "output": {"text": "Nested answer 2"}},
    ]
    with open(temp_file.name, "w") as f:
        json.dump(nested_data, f)
    
    yield temp_file, nested_data
    
    # Clean up the temporary file
    os.unlink(temp_file.name)


@pytest.fixture
def mock_dataset_adapter():
    # Create a mock adapter with 100 items
    mock_adapter = MagicMock()
    mock_adapter.adapt.return_value = [
        {"inputs": {"question": f"Q{i}"}, "outputs": {"answer": f"A{i}"}, "metadata": {}} 
        for i in range(100)
    ]
    return mock_adapter


def test_load_data_simple_fields(simple_data_file):
    # Unpack the fixture
    temp_file, test_data = simple_data_file
    
    # Test with simple field names
    adapter = ConfigurableJSONAdapter(
        dataset_path=temp_file.name,
        input_field="question",
        golden_output_field="answer"
    )
    data = adapter.load_raw_data()
    
    assert len(data) == 2
    # The raw data should have the original fields
    assert data[0]["question"] == "Test question 1"
    assert data[0]["answer"] == "Test answer 1"
    
    # Test the adapt method which returns the standardized format
    adapted_data = adapter.adapt()
    assert len(adapted_data) == 2
    assert adapted_data[0]["inputs"]["question"] == "Test question 1"
    assert adapted_data[0]["outputs"]["answer"] == "Test answer 1"


def test_load_data_nested_fields(nested_data_file):
    # Unpack the fixture
    temp_file, nested_data = nested_data_file
    
    # Test with nested field paths
    adapter = ConfigurableJSONAdapter(
        dataset_path=temp_file.name,
        input_field=["fields", "input"],
        golden_output_field=["output", "text"]
    )
    data = adapter.load_raw_data()
    
    assert len(data) == 2
    # Raw data doesn't have the mapped fields yet
    
    # Test the adapt method which returns the standardized format
    adapted_data = adapter.adapt()
    assert len(adapted_data) == 2
    assert adapted_data[0]["inputs"]["question"] == "Nested question 1"
    assert adapted_data[0]["outputs"]["answer"] == "Nested answer 1"


def test_transform_functions(simple_data_file):
    # Unpack the fixture
    temp_file, test_data = simple_data_file
    
    # Test with transform functions
    def input_transform(text):
        return f"Transformed: {text}"
        
    def output_transform(text):
        return text.upper()
        
    adapter = ConfigurableJSONAdapter(
        dataset_path=temp_file.name,
        input_field="question",
        golden_output_field="answer",
        input_transform=input_transform,
        output_transform=output_transform
    )
    data = adapter.load_raw_data()
    
    # Raw data doesn't have transformed values
    assert data[0]["question"] == "Test question 1"
    assert data[0]["answer"] == "Test answer 1"
    
    # Test the adapt method which applies transformations
    adapted_data = adapter.adapt()
    assert adapted_data[0]["inputs"]["question"] == "Transformed: Test question 1"
    assert adapted_data[0]["outputs"]["answer"] == "TEST ANSWER 1"


def test_load_dataset_default_splits(mock_dataset_adapter):
    # Test dataset loading with default split ratios
    train, val, test = load_dataset(mock_dataset_adapter)
    
    # Check split sizes (default is 60/20/20)
    assert len(train) == 60
    assert len(val) == 20
    assert len(test) == 20


def test_custom_split_ratios(mock_dataset_adapter):
    # Test with custom split ratios
    train, val, test = load_dataset(mock_dataset_adapter, train_size=0.7, validation_size=0.2)
    
    # Check split sizes
    assert len(train) == 70
    assert len(val) == 20
    assert len(test) == 10
