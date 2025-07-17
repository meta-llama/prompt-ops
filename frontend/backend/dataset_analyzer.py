"""
Dataset Analysis Service for Dynamic Field Mapping

This service analyzes uploaded dataset files to detect field structures,
classify field types, and suggest field mappings for different use cases.
"""

import csv
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class FieldInfo:
    """Information about a detected field in the dataset."""

    def __init__(
        self,
        name: str,
        field_type: str,
        sample_values: List[Any],
        coverage: float = 0.0,  # percentage of records that have this field
        populated_count: int = 0,  # number of records with non-null values
        total_count: int = 0,  # total number of records analyzed
    ):
        self.name = name
        self.field_type = field_type  # 'string', 'array', 'object', 'number', 'boolean'
        self.sample_values = sample_values
        self.coverage = coverage  # 0.0 to 1.0 - what % of records have this field
        self.populated_count = populated_count  # how many records have this field
        self.total_count = total_count  # total records analyzed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.field_type,
            "samples": self.sample_values,
            "coverage": self.coverage,
            "populated_count": self.populated_count,
            "total_count": self.total_count,
        }


class DatasetAnalyzer:
    """Analyzes dataset files and provides field mapping suggestions."""

    def __init__(self):
        pass

    def analyze_file(self, file_path: str, sample_size: int = 10) -> Dict[str, Any]:
        """
        Analyze a dataset file and return field information.

        Args:
            file_path: Path to the dataset file
            sample_size: Number of samples to analyze

        Returns:
            Dictionary containing field analysis results
        """
        try:
            # Load data
            data = self._load_data(file_path)
            if not data:
                return {"error": "Could not load or parse file"}

            # For accurate coverage calculation, we need to analyze the full dataset
            # But for performance, we'll analyze a larger sample for coverage
            coverage_sample_size = min(
                len(data), 100
            )  # Use up to 100 records for coverage
            coverage_data = data[:coverage_sample_size]

            # Use smaller sample for field type analysis and sample values
            sample_data = data[:sample_size] if len(data) > sample_size else data

            # Analyze fields with full dataset size for accurate coverage
            fields = self._analyze_fields(coverage_data, len(data))

            return {
                "total_records": len(data),
                "sample_size": len(sample_data),
                "fields": [field.to_dict() for field in fields],
                "suggestions": {},  # Empty suggestions since we removed classification
                "sample_data": sample_data[:3],  # Show first 3 records
            }

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}

    def _load_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from file based on extension."""
        path = Path(file_path)
        extension = path.suffix.lower()

        try:
            if extension == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else [data]

            elif extension == ".csv":
                df = pd.read_csv(file_path)
                return df.to_dict("records")

            elif extension in [".yaml", ".yml"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data if isinstance(data, list) else [data]

            else:
                raise ValueError(f"Unsupported file format: {extension}")

        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            return []

    def _analyze_fields(
        self, data: List[Dict[str, Any]], total_dataset_size: int
    ) -> List[FieldInfo]:
        """Analyze fields in the dataset."""
        if not data:
            return []

        field_info = {}
        sample_size = len(data)

        # First pass: collect all field values without tracking coverage
        for record in data:
            self._extract_fields_recursive(record, field_info, track_coverage=False)

        # Second pass: count how many records have each field (for completeness)
        field_completeness = {}
        for record in data:
            # Get all fields present in this record
            record_fields = set()
            self._get_record_fields(record, record_fields)

            # Count this record for each field it contains
            for field_path in record_fields:
                if field_path not in field_completeness:
                    field_completeness[field_path] = 0
                field_completeness[field_path] += 1

        # Convert to FieldInfo objects
        fields = []
        for field_path, info in field_info.items():
            field_type = self._determine_field_type(info["values"])
            sample_values = self._get_sample_values(info["values"])

            # Calculate coverage: how many records have this field
            populated_count_in_sample = field_completeness.get(field_path, 0)

            # Extrapolate coverage to full dataset
            if sample_size > 0:
                sample_coverage = populated_count_in_sample / sample_size
                estimated_populated_count = int(sample_coverage * total_dataset_size)
                coverage = min(sample_coverage, 1.0)  # Cap at 100%
            else:
                estimated_populated_count = 0
                coverage = 0.0

            fields.append(
                FieldInfo(
                    name=field_path,
                    field_type=field_type,
                    sample_values=sample_values,
                    coverage=coverage,
                    populated_count=estimated_populated_count,
                    total_count=total_dataset_size,
                )
            )

        return fields

    def _extract_fields_recursive(
        self,
        obj: Any,
        field_info: Dict[str, Any],
        prefix: str = "",
        track_coverage: bool = False,
    ):
        """Recursively extract fields from nested objects for value sampling and type detection."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key

                if field_path not in field_info:
                    field_info[field_path] = {"values": []}

                if isinstance(value, (dict, list)):
                    self._extract_fields_recursive(
                        value, field_info, field_path, track_coverage
                    )
                else:
                    # Only add meaningful values to samples
                    if self._has_meaningful_value(value):
                        field_info[field_path]["values"].append(value)

        elif isinstance(obj, list) and obj:
            # Handle arrays - analyze first few elements
            if prefix not in field_info:
                field_info[prefix] = {"values": []}

            for i, item in enumerate(obj[:3]):  # Sample first 3 array elements
                if isinstance(item, dict):
                    self._extract_fields_recursive(
                        item, field_info, prefix, track_coverage
                    )
                else:
                    # Handle arrays of primitives
                    field_info[prefix]["values"].extend(
                        obj[:10]
                    )  # Sample first 10 items
                    break

    def _has_meaningful_value(self, value: Any) -> bool:
        """Check if a value is meaningful (not None, empty string, or empty collection)."""
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True

    def _get_record_fields(self, obj: Any, field_set: set, prefix: str = ""):
        """Get all field paths present in a single record (for completeness calculation)."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key

                # Only count this field if it has meaningful value
                if self._has_meaningful_value(value):
                    field_set.add(field_path)

                # Recursively check nested structures
                if isinstance(value, (dict, list)):
                    self._get_record_fields(value, field_set, field_path)

        elif isinstance(obj, list) and obj:
            # For arrays, if the array is not empty, count it as present
            if prefix:
                field_set.add(prefix)

            # Also check elements for nested fields
            for item in obj[:3]:  # Sample first 3 elements
                if isinstance(item, dict):
                    self._get_record_fields(item, field_set, prefix)

    def _determine_field_type(self, values: List[Any]) -> str:
        """Determine the type of a field based on its values."""
        if not values:
            return "unknown"

        # Sample values to determine type
        sample_values = values[:20]  # Look at first 20 values

        type_counts = Counter()
        for value in sample_values:
            if isinstance(value, str):
                type_counts["string"] += 1
            elif isinstance(value, (int, float)):
                type_counts["number"] += 1
            elif isinstance(value, bool):
                type_counts["boolean"] += 1
            elif isinstance(value, list):
                type_counts["array"] += 1
            elif isinstance(value, dict):
                type_counts["object"] += 1
            else:
                type_counts["unknown"] += 1

        # Return the most common type
        return type_counts.most_common(1)[0][0] if type_counts else "unknown"

    def _get_sample_values(self, values: List[Any], max_samples: int = 5) -> List[Any]:
        """Get sample values for display."""
        if not values:
            return []

        # Filter out None values and get diverse samples
        filtered_values = [v for v in values if v is not None]

        # Get unique values up to max_samples
        unique_values = []
        seen = set()
        for value in filtered_values:
            if len(unique_values) >= max_samples:
                break

            # Convert to string for hashing
            value_str = str(value)[:100]  # Truncate long values
            if value_str not in seen:
                seen.add(value_str)
                unique_values.append(
                    value if len(str(value)) <= 100 else str(value)[:100] + "..."
                )

        return unique_values

    def generate_adapter_config(
        self, mappings: Dict[str, str], use_case: str
    ) -> Dict[str, Any]:
        """Generate ConfigurableJSONAdapter configuration from field mappings."""
        config = {"use_case": use_case, "mappings": mappings}

        if use_case == "qa":
            config["input_field"] = mappings.get("question", "question")
            config["golden_output_field"] = mappings.get("answer", "answer")

        elif use_case == "rag":
            config["question_field"] = mappings.get("query", "query")
            config["context_field"] = mappings.get("context", "context")
            config["golden_answer_field"] = mappings.get("answer", "answer")

        return config

    def preview_transformation(
        self,
        file_path: str,
        mappings: Dict[str, str],
        use_case: str,
        sample_size: int = 5,
    ) -> Dict[str, Any]:
        """Preview how the data will be transformed with given mappings."""
        try:
            # Load sample data
            data = self._load_data(file_path)
            if not data:
                return {"error": "Could not load file"}

            sample_data = data[:sample_size]

            # Generate adapter config
            adapter_config = self.generate_adapter_config(mappings, use_case)

            # Transform sample data
            transformed_data = []
            for record in sample_data:
                transformed_record = self._transform_record(record, mappings, use_case)
                transformed_data.append(transformed_record)

            return {
                "original_data": sample_data,
                "transformed_data": transformed_data,
                "adapter_config": adapter_config,
            }

        except Exception as e:
            logger.error(f"Error previewing transformation: {str(e)}")
            return {"error": f"Preview failed: {str(e)}"}

    def _transform_record(
        self, record: Dict[str, Any], mappings: Dict[str, str], use_case: str
    ) -> Dict[str, Any]:
        """Transform a single record according to mappings."""
        transformed = {"inputs": {}, "outputs": {}, "metadata": {}}

        # Apply mappings
        for target_field, source_field in mappings.items():
            value = self._get_nested_value(record, source_field)

            if target_field in ["query", "context"]:
                transformed["inputs"][target_field] = value
            elif target_field == "answer":
                transformed["outputs"][target_field] = value
            else:
                transformed["metadata"][target_field] = value

        return transformed

    def _get_nested_value(self, obj: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested object using dot notation."""
        keys = field_path.split(".")
        value = obj

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value
