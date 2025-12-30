# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Tests for dataset field validation and type conversion.
"""

import json
import logging
import tempfile
from pathlib import Path

import pytest

from prompt_ops.core.datasets import ConfigurableJSONAdapter, create_dspy_example


class TestDatasetFieldValidation:
    """Test cases for field validation and type conversion in dataset adapters."""

    def test_nested_dict_field_mapping_error_message(self, caplog):
        """
        Test that mapping to a nested dict field produces a helpful error message.

        This test reproduces the issue where a user mapped to 'fields' instead of
        'fields.input', resulting in a dict being assigned to the 'question' field.
        """
        # Create a test dataset with nested structure
        test_data = [
            {"fields": {"input": "What is the capital of France?"}, "answer": "Paris"}
        ]

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            # Create adapter with INCORRECT mapping (maps to 'fields' instead of 'fields.input')
            with caplog.at_level(logging.ERROR):
                adapter = ConfigurableJSONAdapter(
                    dataset_path=temp_path,
                    input_field="fields",  # This is wrong - should be ["fields", "input"]
                    golden_output_field="answer",
                    file_format="json",
                )

                # Adapt the dataset
                result = adapter.adapt()

                # Check that we got an error log with helpful message
                assert any(
                    "contains a dict but should be a string" in record.message
                    for record in caplog.records
                ), "Expected error message about dict field not found in logs"

                assert any(
                    "Did you mean to specify a nested path" in record.message
                    for record in caplog.records
                ), "Expected hint about nested paths not found in logs"

                # Check that the value was JSON-stringified as a fallback
                assert len(result) == 1
                assert "inputs" in result[0]
                # The dict should have been stringified
                question_value = result[0]["inputs"]["question"]
                assert isinstance(question_value, str)
                # It should be a JSON string of the dict
                parsed = json.loads(question_value)
                assert parsed == {"input": "What is the capital of France?"}

        finally:
            Path(temp_path).unlink()

    def test_correct_nested_field_mapping(self):
        """Test that correct nested field mapping works without warnings."""
        # Create a test dataset with nested structure
        test_data = [
            {"fields": {"input": "What is the capital of France?"}, "answer": "Paris"}
        ]

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            # Create adapter with CORRECT mapping
            adapter = ConfigurableJSONAdapter(
                dataset_path=temp_path,
                input_field=["fields", "input"],  # Correct nested path
                golden_output_field="answer",
                file_format="json",
            )

            # Adapt the dataset
            result = adapter.adapt()

            # Check that we got the correct value without stringification
            assert len(result) == 1
            assert "inputs" in result[0]
            question_value = result[0]["inputs"]["question"]
            assert isinstance(question_value, str)
            assert question_value == "What is the capital of France?"

        finally:
            Path(temp_path).unlink()

    def test_numeric_field_conversion(self, caplog):
        """Test that numeric fields are converted to strings with a warning."""
        test_data = [{"question_id": 12345, "answer": "42"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with caplog.at_level(logging.WARNING):
                adapter = ConfigurableJSONAdapter(
                    dataset_path=temp_path,
                    input_field="question_id",
                    golden_output_field="answer",
                    file_format="json",
                )

                result = adapter.adapt()

                # Check for warning about numeric conversion
                assert any(
                    "Converting to string" in record.message
                    for record in caplog.records
                ), "Expected warning about numeric conversion"

                # Check that the value was converted to string
                assert result[0]["inputs"]["question"] == "12345"
                assert isinstance(result[0]["inputs"]["question"], str)

        finally:
            Path(temp_path).unlink()

    def test_list_field_stringification(self, caplog):
        """Test that list fields are JSON-stringified with an error message."""
        test_data = [{"question": ["What", "is", "the", "answer?"], "answer": "42"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with caplog.at_level(logging.ERROR):
                adapter = ConfigurableJSONAdapter(
                    dataset_path=temp_path,
                    input_field="question",
                    golden_output_field="answer",
                    file_format="json",
                )

                result = adapter.adapt()

                # Check for error about list field
                assert any(
                    "contains a list but should be a string" in record.message
                    for record in caplog.records
                ), "Expected error message about list field"

                # Check that the value was JSON-stringified
                question_value = result[0]["inputs"]["question"]
                assert isinstance(question_value, str)
                parsed = json.loads(question_value)
                assert parsed == ["What", "is", "the", "answer?"]

        finally:
            Path(temp_path).unlink()

    def test_none_field_handling(self, caplog):
        """Test that None/null fields are handled gracefully."""
        test_data = [{"question": None, "answer": "42"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with caplog.at_level(logging.WARNING):
                adapter = ConfigurableJSONAdapter(
                    dataset_path=temp_path,
                    input_field="question",
                    golden_output_field="answer",
                    file_format="json",
                    default_value="",
                )

                result = adapter.adapt()

                # Check for warning about None field
                assert any(
                    "is None" in record.message for record in caplog.records
                ), "Expected warning about None field"

                # Check that empty string was used
                assert result[0]["inputs"]["question"] == ""

        finally:
            Path(temp_path).unlink()

    def test_create_dspy_example_validation(self):
        """Test that create_dspy_example validates input structure."""
        # Test missing 'inputs' key
        with pytest.raises(ValueError, match="must contain 'inputs' and 'outputs'"):
            create_dspy_example({"outputs": {"answer": "42"}})

        # Test missing 'outputs' key
        with pytest.raises(ValueError, match="must contain 'inputs' and 'outputs'"):
            create_dspy_example({"inputs": {"question": "What?"}})

        # Test invalid 'inputs' type
        with pytest.raises(ValueError, match="'inputs' must be a dictionary"):
            create_dspy_example({"inputs": "not a dict", "outputs": {"answer": "42"}})

        # Test invalid 'outputs' type
        with pytest.raises(ValueError, match="'outputs' must be a dictionary"):
            create_dspy_example(
                {"inputs": {"question": "What?"}, "outputs": "not a dict"}
            )

    def test_create_dspy_example_type_conversion(self, caplog):
        """Test that create_dspy_example converts non-string values."""
        with caplog.at_level(logging.WARNING):
            doc = {
                "inputs": {"question": {"nested": "dict"}},
                "outputs": {"answer": ["list", "of", "values"]},
            }

            example = create_dspy_example(doc)

            # Check for warnings
            assert any(
                "not a string" in record.message for record in caplog.records
            ), "Expected warnings about non-string values"

            # Check that values were converted
            assert isinstance(example.question, str)
            assert isinstance(example.answer, str)

            # Check that they're valid JSON
            assert json.loads(example.question) == {"nested": "dict"}
            assert json.loads(example.answer) == ["list", "of", "values"]
