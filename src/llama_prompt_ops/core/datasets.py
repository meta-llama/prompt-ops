# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Dataset adapters and utilities for prompt-ops.

This module provides a standardized way to load and process different datasets
for use with the prompt-ops tool.
"""

import json
import csv
import logging
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set, Optional, Union, Callable

import dspy


class DatasetAdapter(ABC):
    """
    Base adapter class for transforming dataset-specific formats into a standardized format.
    
    Subclasses should implement the adapt method to transform their specific dataset
    format into the standardized format expected by the prompt-ops tool.
    """
    
    def __init__(self, dataset_path: str, file_format: str = None):
        """
        Initialize the dataset adapter with a path to the dataset file.
        
        Args:
            dataset_path: Path to the dataset file
            file_format: Format of the file ('json', 'csv', 'yaml'). If None, inferred from file extension.
        """
        self.dataset_path = Path(dataset_path)
        self.file_format = file_format or self._infer_format(self.dataset_path)
        
    def _infer_format(self, path: Path) -> str:
        """
        Infer the file format from the file extension.
        
        Args:
            path: Path to the file
            
        Returns:
            Inferred file format
            
        Raises:
            ValueError: If the file format cannot be inferred
        """
        extension = path.suffix.lower()
        if extension == '.json':
            return 'json'
        elif extension == '.csv':
            return 'csv'
        elif extension in ['.yaml', '.yml']:
            return 'yaml'
        else:
            raise ValueError(f"Unsupported file format: {extension}. Supported formats: .json, .csv, .yaml, .yml")
    
    def _load_json(self) -> List[Dict[str, Any]]:
        """
        Load data from a JSON file.
        
        Returns:
            List of data items
        """
        with open(self.dataset_path, 'r') as f:
            return json.load(f)
    
    def _load_csv(self) -> List[Dict[str, Any]]:
        """
        Load data from a CSV file.
        
        Returns:
            List of data items
        """
        with open(self.dataset_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _load_yaml(self) -> List[Dict[str, Any]]:
        """
        Load data from a YAML file.
        
        Returns:
            List of data items
        """
        with open(self.dataset_path, 'r') as f:
            data = yaml.safe_load(f)
            # Ensure we return a list of dictionaries
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # If the YAML contains a single dictionary with a list field, return that list
                for key, value in data.items():
                    if isinstance(value, list):
                        return value
                # Otherwise, return a list with the dictionary as the only element
                return [data]
            else:
                raise ValueError(f"Unexpected YAML structure: {type(data)}")
        
    def load_raw_data(self) -> List[Dict[str, Any]]:
        """
        Load raw data from the dataset path based on the file format.
        
        Returns:
            List of raw data items from the dataset
            
        Raises:
            ValueError: If the file format is not supported
        """
        loaders = {
            'json': self._load_json,
            'csv': self._load_csv,
            'yaml': self._load_yaml
        }
        
        if self.file_format not in loaders:
            raise ValueError(f"Unsupported file format: {self.file_format}. Supported formats: {', '.join(loaders.keys())}")
        
        return loaders[self.file_format]()
            
    @abstractmethod
    def adapt(self) -> List[Dict[str, Any]]:
        """
        Transform dataset-specific format into standardized format.
        
        The standardized format is a list of dictionaries, where each dictionary
        represents a single example and has the following structure:
        {
            "inputs": {
                "field1": value1,
                "field2": value2,
                ...
            },
            "outputs": {
                "field1": value1,
                "field2": value2,
                ...
            },
            "metadata": {  # Optional
                "field1": value1,
                "field2": value2,
                ...
            }
        }
        
        Returns:
            List of standardized examples
        """
        pass


class ConfigurableJSONAdapter(DatasetAdapter):
    """
    A configurable adapter for JSON datasets with flexible field mappings.
    
    This adapter can be used with any JSON dataset by configuring the input and output
    field mappings. It supports simple field names, nested paths, and custom mappings,
    making it compatible with various JSON structures without requiring custom adapter classes.
    """
    
    def __init__(
        self,
        dataset_path: Union[str, Path],
        input_field: Union[str, List[str], Dict[str, str]],
        golden_output_field: Union[str, List[str], Dict[str, str]],
        file_format: Optional[str] = None,
        input_transform: Optional[Callable] = None,
        output_transform: Optional[Callable] = None,
        default_value: Any = None,
        **kwargs
    ):
        """
        Initialize the standardized JSON adapter.
        
        Args:
            dataset_path: Path to the dataset file
            input_field: Field(s) to use as input. Can be:
                - A string (field name)
                - A list of strings (nested field path)
                - A dict mapping from source fields to destination fields
            golden_output_field: Field(s) to use as ground truth/reference output. Same format options as input_field
            file_format: Format of the dataset file (defaults to json)
            input_transform: Optional function to transform input values
            output_transform: Optional function to transform output values
            **kwargs: Additional arguments
        """
        super().__init__(dataset_path, file_format)
        self.input_field = input_field
        self.golden_output_field = golden_output_field
        self.input_transform = input_transform
        self.output_transform = output_transform
        self.default_value = default_value
    
    def _get_nested_value(self, item: Dict[str, Any], field_path: List[str]) -> Any:
        """
        Get a value from a nested dictionary using a field path.
        
        Args:
            item: Dictionary to extract value from
            field_path: List of keys forming a path to the value
            
        Returns:
            The value at the specified path or default_value if not found
        """
        value = item
        for key in field_path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return self.default_value
        return value
    
    def _extract_value(self, item: Dict[str, Any], field_spec: Union[str, List[str], Dict[str, str]]) -> Any:
        """
        Extract a value using a field specification.
        
        Args:
            item: Dictionary to extract value from
            field_spec: Field specification (string, list, or dict)
            
        Returns:
            The extracted value(s)
        """
        if isinstance(field_spec, str):
            # Simple field name
            return item.get(field_spec, self.default_value)
        elif isinstance(field_spec, list):
            # Nested field path
            return self._get_nested_value(item, field_spec)
        elif isinstance(field_spec, dict):
            # Multiple fields mapping
            result = {}
            for src_field, dst_field in field_spec.items():
                if isinstance(src_field, str):
                    value = item.get(src_field, self.default_value)
                elif isinstance(src_field, list):
                    value = self._get_nested_value(item, src_field)
                else:
                    continue
                result[dst_field] = value
            return result
        return self.default_value
    
    def _transform_value(self, value: Any, transform_func: Optional[Callable]) -> Any:
        """
        Apply transformation with error handling.
        
        Args:
            value: Value to transform
            transform_func: Function to apply to the value
            
        Returns:
            Transformed value or original value if transformation fails
        """
        if transform_func is None or value is None:
            return value
            
        try:
            return transform_func(value)
        except Exception as e:
            logging.warning(f"Error transforming value: {e}")
            return value
    
    def _map_to_standard_format(self, values: Any, field_spec: Union[str, List[str], Dict[str, str]], 
                               is_input: bool = True) -> Dict[str, Any]:
        """
        Map extracted values to the standard format.
        
        Args:
            values: Extracted values (single value or dictionary)
            field_spec: Original field specification (for reference)
            is_input: Whether this is mapping input fields (True) or output fields (False)
            
        Returns:
            Dictionary with standardized field names
        """
        result = {}
        
        if isinstance(values, dict):
            # Values already in dictionary format (from dict field_spec)
            result.update(values)
        else:
            # Single value
            if isinstance(field_spec, str):
                # Keep original field name as well
                result[field_spec] = values
            
            # Add standardized field names for DSPy compatibility
            if is_input:
                result['question'] = values
            else:
                result['answer'] = values
        
        return result
    
    def _process_fields(self, item: Dict[str, Any], field_spec: Union[str, List[str], Dict[str, str]], 
                        transform: Optional[Callable] = None, is_input: bool = True) -> Dict[str, Any]:
        """
        Process fields according to the field specification.
        
        Args:
            item: Dictionary to extract values from
            field_spec: Field specification (string, list, or dict)
            transform: Optional function to transform values
            is_input: Whether this is processing input fields (True) or output fields (False)
            
        Returns:
            Dictionary of processed fields
        """
        # 1. Extract values based on field specification
        extracted_values = self._extract_value(item, field_spec)
        
        # 2. Apply transformation if provided
        transformed_values = self._transform_value(extracted_values, transform)
        
        # 3. Map to standard format
        return self._map_to_standard_format(transformed_values, field_spec, is_input)
    
    def adapt(self) -> List[Dict[str, Any]]:
        """
        Transform the JSON dataset into standardized format.
        
        Returns:
            List of standardized examples
        """
        # Load raw data
        raw_data = self.load_raw_data()
        
        # Transform into standardized format
        standardized_data = []
        for item in raw_data:
            inputs = self._process_fields(item, self.input_field, self.input_transform, is_input=True)
            outputs = self._process_fields(item, self.golden_output_field, self.output_transform, is_input=False)
            
            standardized_example = {
                "inputs": inputs,
                "outputs": outputs,
                "metadata": {}
            }
            standardized_data.append(standardized_example)
        
        return standardized_data


class RAGJSONAdapter(ConfigurableJSONAdapter):
    """
    Adapter for RAG (Retrieval-Augmented Generation) JSON datasets with question, context, and answer fields.
    
    This adapter extends ConfigurableJSONAdapter to handle datasets that include retrieval contexts
    or documents alongside questions and answers. It standardizes the format to be compatible with
    RAG-based evaluation and optimization frameworks.
    """
    
    def __init__(
        self,
        dataset_path: Union[str, Path],
        question_field: Union[str, List[str], Dict[str, str]],
        context_field: Union[str, List[str], Dict[str, str]],
        golden_answer_field: Union[str, List[str], Dict[str, str]],
        file_format: Optional[str] = None,
        question_transform: Optional[Callable] = None,
        context_transform: Optional[Callable] = None,
        answer_transform: Optional[Callable] = None,
        default_value: Any = None,
        **kwargs
    ):
        """
        Initialize the RAG JSON adapter.
        
        Args:
            dataset_path: Path to the dataset file
            question_field: Field(s) to use as question. Can be:
                - A string (field name)
                - A list of strings (nested field path)
                - A dict mapping from source fields to destination fields
            context_field: Field(s) to use as context/documents
            golden_answer_field: Field(s) to use as ground truth/reference answer
            file_format: Format of the dataset file (defaults to json)
            question_transform: Optional function to transform question values
            context_transform: Optional function to transform context values
            answer_transform: Optional function to transform answer values
            default_value: Default value to use when a field is not found
            **kwargs: Additional arguments
        """
        # Initialize with basic fields for backward compatibility
        super().__init__(
            dataset_path=dataset_path,
            input_field=question_field,
            golden_output_field=golden_answer_field,
            file_format=file_format,
            input_transform=question_transform,
            output_transform=answer_transform,
            default_value=default_value,
            **kwargs
        )
        
        # Store RAG-specific fields
        self.question_field = question_field
        self.context_field = context_field
        self.golden_answer_field = golden_answer_field
        self.question_transform = question_transform
        self.context_transform = context_transform
        self.answer_transform = answer_transform
    
    def _map_field_to_standard_name(self, field_data: Dict[str, Any], field_type: str) -> Any:
        """
        Extract the primary value from field data and map it to a standard name.
        
        Args:
            field_data: Dictionary of field data
            field_type: Type of field ('question', 'context', 'answer')
            
        Returns:
            The primary value for the field
        """
        # If the standard name already exists, return it
        if field_type in field_data:
            return field_data[field_type]
        
        # Otherwise, use the first value in the dictionary
        if field_data:
            return next(iter(field_data.values()))
        
        return self.default_value
    
    def adapt(self) -> List[Dict[str, Any]]:
        """
        Transform the JSON dataset into standardized format with question, context, and answer.
        
        Returns:
            List of standardized examples with question, context, and answer fields
        """
        # Load raw data
        raw_data = self.load_raw_data()
        
        # Transform into standardized format
        standardized_data = []
        for item in raw_data:
            # Process question, context, and answer fields
            question_data = self._process_fields(item, self.question_field, self.question_transform, is_input=True)
            context_data = self._process_fields(item, self.context_field, self.context_transform, is_input=True)
            answer_data = self._process_fields(item, self.golden_answer_field, self.answer_transform, is_input=False)
            
            # Create standardized inputs with question and context
            inputs = {}
            inputs.update(question_data)  # Include all question fields
            
            # Ensure 'question' field exists
            if 'question' not in inputs:
                inputs['question'] = self._map_field_to_standard_name(question_data, 'question')
            
            # Add context fields
            context_value = self._map_field_to_standard_name(context_data, 'context')
            inputs['context'] = context_value
            
            # Create standardized outputs
            outputs = {}
            outputs.update(answer_data)  # Include all answer fields
            
            # Ensure 'answer' field exists
            if 'answer' not in outputs:
                outputs['answer'] = self._map_field_to_standard_name(answer_data, 'answer')
            
            # Create standardized example
            standardized_example = {
                "inputs": inputs,
                "outputs": outputs,
                "metadata": {}
            }
            standardized_data.append(standardized_example)
        
        return standardized_data


def create_dspy_example(doc: Dict[str, Any]) -> dspy.Example:
    """
    Convert a standardized document into a DSPy example.
    
    Args:
        doc: Standardized document
        
    Returns:
        DSPy example
    """
    # Create example with inputs and outputs
    example = dspy.Example(**doc["inputs"], **doc["outputs"])
    
    # Set input and output keys explicitly
    example._input_keys = set(doc["inputs"].keys())
    example._output_keys = set(doc["outputs"].keys())
    
    # Add metadata if available
    if "metadata" in doc:
        for key, value in doc["metadata"].items():
            setattr(example, key, value)
    
    return example


def load_dataset(
    adapter: DatasetAdapter, 
    train_size: float = 0.60, 
    validation_size: float = 0.20,
    seed: int = 42
) -> Tuple[List[dspy.Example], List[dspy.Example], List[dspy.Example]]:
    """
    Load dataset using an adapter and split into train, validation, and test sets.
    
    Args:
        adapter: Dataset adapter
        train_size: Fraction of data to use for training
        validation_size: Fraction of data to use for validation
        seed: Random seed for shuffling
        
    Returns:
        Tuple containing (trainset, valset, testset)
    """
    # Get standardized data
    data = adapter.adapt()
    logging.info(f"Loaded {len(data)} examples from {adapter.dataset_path}")
    
    # Convert to DSPy examples
    dspy_dataset = [create_dspy_example(doc) for doc in data]
    
    # Split dataset
    total = len(dspy_dataset)
    train_end = int(total * train_size)
    val_end = train_end + int(total * validation_size)
    
    trainset = dspy_dataset[:train_end]
    valset = dspy_dataset[train_end:val_end]
    testset = dspy_dataset[val_end:]
    
    logging.info(f"Created dataset splits:")
    logging.info(f"  - Training:   {len(trainset)} examples ({train_size*100:.1f}% of total)")
    logging.info(f"  - Validation: {len(valset)} examples ({validation_size*100:.1f}% of total)")
    logging.info(f"  - Testing:    {len(testset)} examples ({(1-train_size-validation_size)*100:.1f}% of total)")
    
    return trainset, valset, testset
