import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from llama_prompt_ops.core.migrator import PromptMigrator
from llama_prompt_ops.core.utils import json_to_yaml_file
from llama_prompt_ops.core.utils.format_utils import convert_json_to_yaml


class TestPromptMigrator(unittest.TestCase):
    def setUp(self):
        # Create temporary files for testing
        self.temp_json_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_yaml_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        
        # Sample prompt data in JSON format
        self.prompt_data = {
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
        with open(self.temp_json_file.name, "w") as f:
            json.dump(self.prompt_data, f)
            
    def tearDown(self):
        # Clean up temporary files
        os.unlink(self.temp_json_file.name)
        os.unlink(self.temp_yaml_file.name)
        
    def test_load_prompt_from_json(self):
        # Test loading prompt from JSON file
        migrator = PromptMigrator()
        prompt_data = migrator.load_prompt(self.temp_json_file.name)
        
        self.assertEqual(prompt_data["prompt"], self.prompt_data["prompt"])
        self.assertEqual(prompt_data["metadata"]["name"], self.prompt_data["metadata"]["name"])
        
    @patch('llama_prompt_ops.core.utils.json_to_yaml_file')
    def test_save_optimized_prompt(self, mock_json_to_yaml):
        # Test saving optimized prompt to YAML
        migrator = PromptMigrator()
        
        # Create a mock program with the necessary attributes
        mock_program = MagicMock()
        mock_program.predict.signature.instructions = "Improved prompt: {{question}}"
        mock_program.predict.demos = []
        migrator._optimized_program = mock_program
        
        # Save to YAML
        migrator.save_optimized_prompt(file_path=self.temp_yaml_file.name, save_yaml=True)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.temp_yaml_file.name))
        
        # Verify json_to_yaml_file was called
        mock_json_to_yaml.assert_called_once()
        
        # Verify JSON content
        with open(self.temp_yaml_file.name, "r") as f:
            content = f.read()
            self.assertIn("Improved prompt: {{question}}", content)
        
    @patch("llama_prompt_ops.core.migrator.json_to_yaml_file")
    def test_migrator_uses_utils_function(self, mock_json_to_yaml):
        # Test that migrator uses the utility function for conversion
        migrator = PromptMigrator()
        
        # Create a mock program with the necessary attributes
        mock_program = MagicMock()
        mock_program.predict.signature.instructions = "Test prompt"
        mock_program.predict.demos = []
        migrator._optimized_program = mock_program
        
        # Call save_optimized_prompt
        migrator.save_optimized_prompt(file_path=self.temp_yaml_file.name, save_yaml=True)
        
        # Verify the utility function was called
        mock_json_to_yaml.assert_called_once()


class TestFormatUtils(unittest.TestCase):
    def test_convert_json_to_yaml(self):
        # Test JSON to YAML conversion
        json_data = {
            "prompt": "Test prompt",
            "metadata": {"name": "Test", "version": "1.0"},
            "examples": [{"input": "test", "output": "result"}]
        }
        
        yaml_str = convert_json_to_yaml(json_data)
        
        # Basic checks for YAML format
        self.assertIn("prompt: 'Test prompt'", yaml_str)
        self.assertIn("name: Test", yaml_str)
        self.assertIn("version: '1.0'", yaml_str)
        self.assertIn("- input: test", yaml_str)
        self.assertIn("  output: result", yaml_str)
        
    def test_json_to_yaml_file(self):
        # Test file-based conversion
        temp_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        temp_yaml = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        
        json_data = {"key": "value", "nested": {"item": "data"}}
        
        try:
            # Write JSON data
            with open(temp_json.name, "w") as f:
                json.dump(json_data, f)
                
            # Convert to YAML
            json_to_yaml_file(temp_json.name, temp_yaml.name)
            
            # Verify YAML file
            with open(temp_yaml.name, "r") as f:
                yaml_content = f.read()
                
            self.assertIn("key: value", yaml_content)
            self.assertIn("item: data", yaml_content)
            
        finally:
            # Clean up
            os.unlink(temp_json.name)
            os.unlink(temp_yaml.name)
