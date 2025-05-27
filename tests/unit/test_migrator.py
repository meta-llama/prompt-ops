import json
import os
import tempfile
import pytest

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
    
    # Test loading prompt from JSON file
    migrator = PromptMigrator()
    loaded_prompt_data = migrator.load_prompt(file.name)
    
    assert loaded_prompt_data["prompt"] == prompt_data["prompt"]
    assert loaded_prompt_data["metadata"]["name"] == prompt_data["metadata"]["name"]


@patch('llama_prompt_ops.core.utils.json_to_yaml_file')
def test_save_optimized_prompt(mock_json_to_yaml, temp_yaml_file):
    # Test saving optimized prompt to YAML
    migrator = PromptMigrator()
    
    # Create a mock program with the necessary attributes
    mock_program = MagicMock()
    mock_program.predict.signature.instructions = "Improved prompt: {{question}}"
    mock_program.predict.demos = []
    migrator._optimized_program = mock_program
    
    # Save to YAML
    migrator.save_optimized_prompt(file_path=temp_yaml_file.name, save_yaml=True)
    
    # Verify file was created
    assert os.path.exists(temp_yaml_file.name)
    
    # Verify json_to_yaml_file was called
    mock_json_to_yaml.assert_called_once()
    
    # Verify JSON content
    with open(temp_yaml_file.name, "r") as f:
        content = f.read()
        assert "Improved prompt: {{question}}" in content


@patch("llama_prompt_ops.core.migrator.json_to_yaml_file")
def test_migrator_uses_utils_function(mock_json_to_yaml, temp_yaml_file):
    # Test that migrator uses the utility function for conversion
    migrator = PromptMigrator()
    
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
    json_data = {
        "prompt": "Test prompt",
        "metadata": {"name": "Test", "version": "1.0"},
        "examples": [{"input": "test", "output": "result"}]
    }
    
    yaml_str = convert_json_to_yaml(json_data)
    
    # Basic checks for YAML format
    assert "prompt: 'Test prompt'" in yaml_str
    assert "name: Test" in yaml_str
    assert "version: '1.0'" in yaml_str
    assert "- input: test" in yaml_str
    assert "  output: result" in yaml_str


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
    
    # Test data
    json_data = {"key": "value", "nested": {"item": "data"}}
    
    # Write JSON data
    with open(temp_json.name, "w") as f:
        json.dump(json_data, f)
        
    # Convert to YAML
    json_to_yaml_file(temp_json.name, temp_yaml.name)
    
    # Verify YAML file
    with open(temp_yaml.name, "r") as f:
        yaml_content = f.read()
        
    assert "key: value" in yaml_content
    assert "item: data" in yaml_content
