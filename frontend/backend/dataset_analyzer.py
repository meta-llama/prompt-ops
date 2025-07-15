"""
Dataset Analysis Service for Dynamic Field Mapping

This service analyzes uploaded dataset files to detect field structures,
classify field types, and suggest field mappings for different use cases.
"""

import csv
import json
import logging
import re
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
        confidence: float = 0.0,
        suggested_mapping: Optional[str] = None,
    ):
        self.name = name
        self.field_type = field_type  # 'string', 'array', 'object', 'number', 'boolean'
        self.sample_values = sample_values
        self.confidence = confidence  # 0.0 to 1.0
        self.suggested_mapping = (
            suggested_mapping  # 'question', 'answer', 'context', etc.
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.field_type,
            "samples": self.sample_values,
            "confidence": self.confidence,
            "suggested_mapping": self.suggested_mapping,
        }


class DatasetAnalyzer:
    """Analyzes dataset files and provides field mapping suggestions."""

    def __init__(self):
        # Heuristic patterns for field classification
        self.field_patterns = {
            "question": [
                r"question",
                r"query",
                r"q\b",
                r"input",
                r"prompt",
                r"user",
                r"request",
                r"ask",
                r"inquiry",
                r"problem",
            ],
            "answer": [
                r"answer",
                r"response",
                r"output",
                r"reply",
                r"solution",
                r"result",
                r"completion",
                r"assistant",
                r"target",
            ],
            "context": [
                r"context",
                r"document",
                r"passage",
                r"text",
                r"content",
                r"background",
                r"reference",
                r"source",
                r"material",
            ],
            "documents": [
                r"documents",
                r"docs",
                r"passages",
                r"texts",
                r"materials",
                r"sources",
                r"references",
                r"corpus",
            ],
            "id": [r"id", r"idx", r"index", r"identifier", r"key", r"uid"],
        }

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

            # Sample data for analysis
            sample_data = data[:sample_size] if len(data) > sample_size else data

            # Analyze fields
            fields = self._analyze_fields(sample_data)

            # Classify fields using heuristics
            classified_fields = self._classify_fields(fields)

            # Generate suggestions for each use case
            suggestions = self._generate_use_case_suggestions(classified_fields)

            return {
                "total_records": len(data),
                "sample_size": len(sample_data),
                "fields": [field.to_dict() for field in classified_fields],
                "suggestions": suggestions,
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

    def _analyze_fields(self, data: List[Dict[str, Any]]) -> List[FieldInfo]:
        """Analyze fields in the dataset."""
        if not data:
            return []

        field_info = {}

        for record in data:
            self._extract_fields_recursive(record, field_info)

        # Convert to FieldInfo objects
        fields = []
        for field_path, info in field_info.items():
            field_type = self._determine_field_type(info["values"])
            sample_values = self._get_sample_values(info["values"])

            fields.append(
                FieldInfo(
                    name=field_path, field_type=field_type, sample_values=sample_values
                )
            )

        return fields

    def _extract_fields_recursive(
        self, obj: Any, field_info: Dict[str, Any], prefix: str = ""
    ):
        """Recursively extract fields from nested objects."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key

                if field_path not in field_info:
                    field_info[field_path] = {"values": []}

                if isinstance(value, (dict, list)):
                    self._extract_fields_recursive(value, field_info, field_path)
                else:
                    field_info[field_path]["values"].append(value)

        elif isinstance(obj, list) and obj:
            # Handle arrays - analyze first few elements
            for i, item in enumerate(obj[:3]):  # Sample first 3 array elements
                if isinstance(item, dict):
                    self._extract_fields_recursive(item, field_info, prefix)
                else:
                    # Handle arrays of primitives
                    if prefix not in field_info:
                        field_info[prefix] = {"values": []}
                    field_info[prefix]["values"].extend(
                        obj[:10]
                    )  # Sample first 10 items
                    break

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

    def _classify_fields(self, fields: List[FieldInfo]) -> List[FieldInfo]:
        """Classify fields using heuristic patterns."""
        for field in fields:
            best_match = None
            best_confidence = 0.0

            # Check field name against patterns
            field_name_lower = field.name.lower()

            for category, patterns in self.field_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, field_name_lower):
                        confidence = self._calculate_confidence(field, category)
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = category

            field.suggested_mapping = best_match
            field.confidence = best_confidence

        return fields

    def _calculate_confidence(self, field: FieldInfo, category: str) -> float:
        """Calculate confidence score for a field mapping."""
        base_confidence = 0.7  # Base confidence for pattern match

        # Adjust confidence based on field type
        if (
            category in ["question", "answer", "context"]
            and field.field_type == "string"
        ):
            base_confidence += 0.2
        elif category == "documents" and field.field_type == "array":
            base_confidence += 0.2
        elif category == "id" and field.field_type in ["string", "number"]:
            base_confidence += 0.1

        # Adjust based on sample values
        if field.sample_values:
            avg_length = sum(len(str(v)) for v in field.sample_values) / len(
                field.sample_values
            )

            if category in ["question", "answer", "context"]:
                # Expect longer text for these fields
                if avg_length > 10:
                    base_confidence += 0.1
            elif category == "id":
                # Expect shorter values for IDs
                if avg_length < 20:
                    base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _generate_use_case_suggestions(self, fields: List[FieldInfo]) -> Dict[str, Any]:
        """Generate field mapping suggestions for different use cases."""
        suggestions = {
            "qa": {
                "required": ["question", "answer"],
                "optional": ["id", "metadata"],
                "mappings": {},
            },
            "rag": {
                "required": ["question", "documents", "answer"],
                "optional": ["id", "metadata"],
                "mappings": {},
            },
            "custom": {"required": [], "optional": [], "mappings": {}},
        }

        # Create mapping suggestions for each use case
        for use_case, config in suggestions.items():
            if use_case == "custom":
                continue

            for required_field in config["required"]:
                best_field = self._find_best_field_match(fields, required_field)
                if best_field:
                    config["mappings"][required_field] = {
                        "source_field": best_field.name,
                        "confidence": best_field.confidence,
                    }

        return suggestions

    def _find_best_field_match(
        self, fields: List[FieldInfo], target_field: str
    ) -> Optional[FieldInfo]:
        """Find the best field match for a target field."""
        candidates = [f for f in fields if f.suggested_mapping == target_field]

        if not candidates:
            return None

        # Return the candidate with highest confidence
        return max(candidates, key=lambda f: f.confidence)

    def generate_adapter_config(
        self, mappings: Dict[str, str], use_case: str
    ) -> Dict[str, Any]:
        """Generate ConfigurableJSONAdapter configuration from field mappings."""
        config = {"use_case": use_case, "mappings": mappings}

        if use_case == "qa":
            config["input_field"] = mappings.get("question", "question")
            config["golden_output_field"] = mappings.get("answer", "answer")

        elif use_case == "rag":
            config["question_field"] = mappings.get("question", "question")
            config["context_field"] = mappings.get("documents", "documents")
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

            if target_field in ["question", "documents", "context"]:
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
