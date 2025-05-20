import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from llama_prompt_ops.core.datasets import (
    DatasetAdapter,
    ConfigurableJSONAdapter,
    load_dataset
)


class TestConfigurableJSONAdapter(unittest.TestCase):
    def setUp(self):
        # Create a temporary JSON file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.test_data = [
            {"question": "Test question 1", "answer": "Test answer 1"},
            {"question": "Test question 2", "answer": "Test answer 2"},
        ]
        with open(self.temp_file.name, "w") as f:
            json.dump(self.test_data, f)
        
    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.temp_file.name)
        
    def test_load_data_simple_fields(self):
        # Test with simple field names
        adapter = ConfigurableJSONAdapter(
            path=self.temp_file.name,
            input_field="question",
            output_field="answer"
        )
        data = adapter.load_data()
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["question"], "Test question 1")
        self.assertEqual(data[0]["answer"], "Test answer 1")
        
    def test_load_data_nested_fields(self):
        # Create a temporary JSON file with nested fields
        nested_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        nested_data = [
            {"fields": {"input": "Nested question 1"}, "output": {"text": "Nested answer 1"}},
            {"fields": {"input": "Nested question 2"}, "output": {"text": "Nested answer 2"}},
        ]
        with open(nested_temp_file.name, "w") as f:
            json.dump(nested_data, f)
            
        try:
            # Test with nested field paths
            adapter = ConfigurableJSONAdapter(
                path=nested_temp_file.name,
                input_field=["fields", "input"],
                output_field=["output", "text"]
            )
            data = adapter.load_data()
            
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["question"], "Nested question 1")
            self.assertEqual(data[0]["answer"], "Nested answer 1")
        finally:
            os.unlink(nested_temp_file.name)
            
    def test_transform_functions(self):
        # Test with transform functions
        def input_transform(text):
            return f"Transformed: {text}"
            
        def output_transform(text):
            return text.upper()
            
        adapter = ConfigurableJSONAdapter(
            path=self.temp_file.name,
            input_field="question",
            output_field="answer",
            input_transform=input_transform,
            output_transform=output_transform
        )
        data = adapter.load_data()
        
        self.assertEqual(data[0]["question"], "Transformed: Test question 1")
        self.assertEqual(data[0]["answer"], "TEST ANSWER 1")


class TestDatasetLoading(unittest.TestCase):
    def test_load_dataset(self):
        # Create a mock adapter
        mock_adapter = MagicMock()
        mock_adapter.adapt.return_value = [
            {"inputs": {"question": f"Q{i}"}, "outputs": {"answer": f"A{i}"}, "metadata": {}} 
            for i in range(100)
        ]
        
        # Test dataset loading with default split ratios
        train, val, test = load_dataset(mock_adapter)
        
        # Check split sizes (default is 60/20/20)
        self.assertEqual(len(train), 60)
        self.assertEqual(len(val), 20)
        self.assertEqual(len(test), 20)
        
    def test_custom_split_ratios(self):
        # Create a mock adapter
        mock_adapter = MagicMock()
        mock_adapter.adapt.return_value = [
            {"inputs": {"question": f"Q{i}"}, "outputs": {"answer": f"A{i}"}, "metadata": {}} 
            for i in range(100)
        ]
        
        # Test with custom split ratios
        train, val, test = load_dataset(mock_adapter, train_size=0.7, validation_size=0.2)
        
        # Check split sizes
        self.assertEqual(len(train), 70)
        self.assertEqual(len(val), 20)
        self.assertEqual(len(test), 10)
