"""
Dataset adapters and utilities for prompt migrator.

This module provides a standardized way to load and process different datasets
for use with the prompt migrator.
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
    format into the standardized format expected by the prompt migrator.
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
    train_size: float = 0.25, 
    validation_size: float = 0.25,
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
