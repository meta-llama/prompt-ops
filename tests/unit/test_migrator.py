import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Mock the BaseStrategy class before importing PromptMigrator
with patch('llama_prompt_ops.core.prompt_strategies.BaseStrategy') as MockBaseStrategy:
    # Make the mock return itself when instantiated
    MockBaseStrategy.return_value = MockBaseStrategy
    # Import after patching
    from llama_prompt_ops.core.migrator import PromptMigrator

from llama_prompt_ops.core.utils import json_to_yaml_file
from llama_prompt_ops.core.utils.format_utils import convert_json_to_yaml


@pytest.fixture
def temp_json_file():
    # Create temporary file for testing
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    
    # Sample prompt data in JSON format
    prompt_data = {
        "prompt": "Answer the following question: {{question}}",
        "metadata": {
            "name": "Test Prompt",
            "version": "1.0",
            "description": "A test prompt for unit testing"
        },
        "examples": [
            {"question": "What is AI?", "answer": "AI stands for Artificial Intelligence."}
        ]
    }
    
    # Write sample data to JSON file
    with open(file.name, "w") as f:
        json.dump(prompt_data, f)
    
    yield file, prompt_data
    
    # Clean up temporary file
    os.unlink(file.name)


@pytest.fixture
def temp_yaml_file():
    # Create temporary file for testing
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    
    yield file
    
    # Clean up temporary file
    os.unlink(file.name)


def test_load_prompt_from_json(temp_json_file):
    # Unpack the fixture
    file, prompt_data = temp_json_file
    
    # Since the PromptMigrator no longer has a load_prompt method,
    # we'll test loading JSON directly
    with open(file.name, 'r') as f:
        loaded_data = json.load(f)
    
    # Verify the loaded data matches the expected data
    assert loaded_data["prompt"] == prompt_data["prompt"]
    assert loaded_data["metadata"]["name"] == prompt_data["metadata"]["name"]


@patch('llama_prompt_ops.core.migrator.json_to_yaml_file')
def test_save_optimized_prompt(mock_json_to_yaml, temp_yaml_file):
    # Test saving optimized prompt to YAML
    
    # Create a mock strategy
    mock_strategy = MagicMock()
    mock_strategy.run.return_value = "Optimized prompt"
    
    migrator = PromptMigrator(strategy=mock_strategy)
    
    # Create a mock program with the necessary attributes
    mock_program = MagicMock()
    mock_program.predict = MagicMock()
    mock_program.predict.signature = MagicMock()
    mock_program.predict.signature.instructions = "Improved prompt: {{question}}"
    mock_program.predict.demos = []
    migrator._optimized_program = mock_program
    
    # Save to YAML
    migrator.save_optimized_prompt(file_path=temp_yaml_file.name, save_yaml=True)
    
    # Verify file was created
    assert os.path.exists(temp_yaml_file.name)
    
    # Verify json_to_yaml_file was called with the correct arguments
    mock_json_to_yaml.assert_called_once()
    
    # Since we're mocking json_to_yaml_file, we can't verify the actual content
    # Instead, let's verify that the call arguments match what we expect
    call_args = mock_json_to_yaml.call_args
    assert call_args is not None
    
    # Extract the basename of the file to check if it's included in the call args
    # This is because the save_optimized_prompt method modifies the path to include a "results" directory
    file_basename = os.path.basename(temp_yaml_file.name)
    assert file_basename in str(call_args)


@patch("llama_prompt_ops.core.migrator.json_to_yaml_file")
def test_migrator_uses_utils_function(mock_json_to_yaml, temp_yaml_file):
    # Test that migrator uses the utility function for conversion
    
    # Create a mock strategy
    mock_strategy = MagicMock()
    mock_strategy.run.return_value = "Optimized prompt"
    
    migrator = PromptMigrator(strategy=mock_strategy)
    
    # Create a mock program with the necessary attributes
    mock_program = MagicMock()
    mock_program.predict.signature.instructions = "Test prompt"
    mock_program.predict.demos = []
    migrator._optimized_program = mock_program
    
    # Call save_optimized_prompt
    migrator.save_optimized_prompt(file_path=temp_yaml_file.name, save_yaml=True)
    
    # Verify the utility function was called
    mock_json_to_yaml.assert_called_once()


def test_convert_json_to_yaml():
    # Test JSON to YAML conversion
    prompt = "Test prompt"
    few_shots = [
        {"question": "test", "answer": "result"}
    ]
    
    yaml_str = convert_json_to_yaml(prompt, few_shots)
    
    # Basic checks for YAML format
    assert "Test prompt" in yaml_str
    assert "test" in yaml_str
    assert "result" in yaml_str


@pytest.fixture
def json_yaml_temp_files():
    # Create temporary files for testing
    temp_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    temp_yaml = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    
    yield temp_json, temp_yaml
    
    # Clean up
    os.unlink(temp_json.name)
    os.unlink(temp_yaml.name)


def test_json_to_yaml_file(json_yaml_temp_files):
    # Unpack the fixture
    temp_json, temp_yaml = json_yaml_temp_files
    
    # Test data with the expected format for the new json_to_yaml_file function
    json_data = {"prompt": "Test prompt", "few_shots": []}
    
    # Write JSON data
    with open(temp_json.name, "w") as f:
        json.dump(json_data, f)
        
    # Convert to YAML
    json_to_yaml_file(temp_json.name, temp_yaml.name)
    
    # Verify YAML file
    with open(temp_yaml.name, "r") as f:
        yaml_content = f.read()
        
    # Check for the basic structure in the new YAML format
    assert "system: |-" in yaml_content
    assert "Test prompt" in yaml_content
    assert "Few-shot examples:" in yaml_content
