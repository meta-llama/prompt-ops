# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Metrics for evaluating prompt optimization performance.

This module contains the base metric class and various implementations
for evaluating the quality of optimized prompts.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List, Callable, TypeVar, Generic, Type, get_type_hints
import dspy
from llama_prompt_ops.core.model import ModelAdapter


T = TypeVar('T', bound=Any)
U = TypeVar('U', bound=Any)


class MetricBase(ABC, Generic[T, U]):
    """Base class for all optimization metrics.
    
    This class can be used in two ways:
    1. Return a dictionary of scores (original behavior)
    2. Return a single float score (simplified behavior)
    
    It also supports different input types, including raw values, dictionaries,
    or structured objects like DSPy examples.
    """
    
    @abstractmethod
    def __call__(
        self, 
        gold: T, 
        pred: U, 
        trace: bool = False,
        **kwargs
    ) -> Union[Dict[str, float], float]:
        """
        Evaluate the prediction against the ground truth.
        
        Args:
            gold: Ground truth example. Can be a raw value, dictionary, or object
                 with specific attributes (like a DSPy example)
            pred: Predicted example. Can be a raw value, dictionary, or object
                 with specific attributes (like a DSPy example)
            trace: Whether to enable tracing for debugging
            **kwargs: Additional metric-specific parameters
            
        Returns:
            Either a dictionary containing metric scores or a single float score
        """
        pass
    
    @property
    def name(self) -> str:
        """Return the name of the metric."""
        return self.__class__.__name__
    
    def extract_value(self, obj: Any, key: str, default: Any = None) -> Any:
        """
        Extract a value from an object, which could be a dictionary or an object with attributes.
        
        Args:
            obj: The object to extract from
            key: The key or attribute name to extract
            default: Default value if the key doesn't exist
            
        Returns:
            The extracted value or the default
        """
        if hasattr(obj, key):
            return getattr(obj, key)
        elif isinstance(obj, dict) and key in obj:
            return obj[key]
        return default


class DSPyMetricAdapter(MetricBase):
    """
    Adapter for DSPy-based metrics with flexible configuration.
    
    This adapter encapsulates DSPy dependencies and provides a reusable way to evaluate
    predictions using DSPy's LLM interface. It supports both built-in signatures and
    custom configurations for maximum flexibility.
    
    Args:
        model: DSPy-compatible language model to use for evaluation
        signature_class: Optional custom DSPy Signature class
        signature_name: Name of built-in signature to use (if signature_class not provided)
        input_mapping: Dictionary mapping adapter inputs to signature fields
        output_fields: List of output field names to extract from signature
        score_range: Expected score range from the LLM (min, max)
        normalize_to: Range to normalize scores to (min, max)
        custom_instructions: Optional custom instructions for the signature
    """
    
    # Built-in signature templates
    SIGNATURES = {
        "similarity": {
            "input_fields": {
                "output": "The predicted answer",
                "ground_truth": "The expected ground truth answer"
            },
            "output_fields": {
                "score": "Semantic similarity score from 1-10"
            },
            "instructions": """You are a smart language model that evaluates the similarity between a predicted text and the expected ground truth answer. You do not propose changes to the answer and only critically evaluate the existing answer and provide feedback following the instructions given.

            The following is the response provided by a language model to a prompt:
            {output}

            The expected answer to this prompt is:
            {ground_truth}

            Answer only with an integer from 1 to 10 based on how semantically similar the responses are to the expected answer. where 1 is no semantic similarity at all and 10 is perfect agreement between the responses and the expected answer. On a NEW LINE, give the integer score and nothing more."""
        },
        "correctness": {
            "input_fields": {
                "output": "The predicted answer",
                "ground_truth": "The expected ground truth answer"
            },
            "output_fields": {
                "score": "Correctness score from 1-10"
            },
            "instructions": """You are a smart language model that evaluates the correctness of a predicted answer compared to the expected ground truth. You do not propose changes to the answer and only critically evaluate the existing answer.

            The following is the response provided by a language model to a prompt:
            {output}

            The expected answer to this prompt is:
            {ground_truth}

            Answer only with an integer from 1 to 10 based on how correct the response is compared to the expected answer, where 1 means completely incorrect and 10 means perfectly correct. On a NEW LINE, give the integer score and nothing more."""
        }
    }
    
    def __init__(
        self,
        model=None,
        signature_class=None,
        signature_name=None,
        input_mapping=None,
        output_fields=None,
        score_range=(1, 10),
        normalize_to=(0, 1),
        custom_instructions=None
    ):
        # Handle both raw DSPy models and our ModelAdapter instances
        if isinstance(model, ModelAdapter):
            # If it's a ModelAdapter, we can use its underlying model
            if hasattr(model, '_model'):
                self.model = model._model
            else:
                raise ValueError("Model adapter does not have an accessible underlying model")
        else:
            # If it's a raw model, use it directly
            self.model = model
            
        self.signature_class = signature_class
        self.signature_name = signature_name
        
        # Set default input mapping if not provided
        self.input_mapping = input_mapping or {"pred": "output", "gold": "ground_truth"}
        
        # Set default output fields if not provided
        self.output_fields = output_fields or ["score"]
        
        # Set score range and normalization range
        self.score_range = score_range
        self.normalize_to = normalize_to
        
        # Set custom instructions if provided
        self.custom_instructions = custom_instructions
        
        # Input field descriptions (used for building custom signatures)
        self.input_field_descriptions = {}
        
        # Initialize signature template if a built-in name is provided
        if signature_name and signature_name in self.SIGNATURES:
            template = self.SIGNATURES[signature_name]
            self.input_field_descriptions = template["input_fields"]
            if not output_fields:
                self.output_fields = list(template["output_fields"].keys())
            if not custom_instructions:
                self.custom_instructions = template["instructions"]
    
    def build_custom_signature(self):
        """Build a custom signature class based on configuration."""
        
        # Define input and output fields
        input_fields = {
            name: dspy.InputField(desc=desc) 
            for name, desc in self.input_field_descriptions.items()
        }
        
        output_fields = {}
        if self.signature_name and self.signature_name in self.SIGNATURES:
            # Use output field descriptions from template
            template = self.SIGNATURES[self.signature_name]
            for name, desc in template["output_fields"].items():
                if name in self.output_fields:
                    output_fields[name] = dspy.OutputField(desc=desc)
        else:
            # Create default output fields
            for name in self.output_fields:
                output_fields[name] = dspy.OutputField(
                    desc=f"Score from {self.score_range[0]}-{self.score_range[1]}"
                )
        
        # Create signature class dynamically
        attrs = {
            **input_fields,
            **output_fields,
            "__doc__": self.custom_instructions or self._default_instructions()
        }
        
        return type("CustomSignature", (dspy.Signature,), attrs)
    
    def _default_instructions(self):
        """Generate default instructions based on configuration."""
        input_placeholders = "\n\n".join(
            f"{name.capitalize()}: {{{name}}}" 
            for name in self.input_field_descriptions.keys()
        )
        
        output_placeholders = "\n".join(
            f"{name.capitalize()}[{self.score_range[0]}-{self.score_range[1]}]:" 
            for name in self.output_fields
        )
        
        return f"""Evaluate the similarity between the inputs.
Score from {self.score_range[0]}-{self.score_range[1]}, where {self.score_range[0]} means completely different 
and {self.score_range[1]} means identical in meaning.

{input_placeholders}

{output_placeholders}"""
    
    def normalize_score(self, score):
        """Normalize score from score_range to normalize_to range."""
        min_score, max_score = self.score_range
        min_norm, max_norm = self.normalize_to
        
        # Handle edge cases
        if min_score == max_score:
            return min_norm
        
        # Normalize the score
        normalized = ((score - min_score) / (max_score - min_score)) * (max_norm - min_norm) + min_norm
        
        # Clamp to the target range
        return max(min_norm, min(max_norm, normalized))
    
    def extract_value(self, obj, key, default=None):
        """Extract a value from an object, handling different object types."""
        if hasattr(obj, key):
            return getattr(obj, key)
        elif isinstance(obj, dict) and key in obj:
            return obj[key]
        return default
    
    def __call__(self, gold: Any, pred: Any, trace: bool = False, **kwargs) -> float:
        """
        Evaluate the prediction against the ground truth using DSPy.
        
        Args:
            gold: Ground truth example
            pred: Predicted example
            trace: Whether to enable tracing
            
        Returns:
            A float score between normalize_to[0] and normalize_to[1]
        """
        try:            
            # Extract values from objects based on input mapping
            inputs = {}
            for adapter_key, sig_key in self.input_mapping.items():
                if adapter_key == "gold":
                    inputs[sig_key] = self.extract_value(gold, "answer", gold)
                elif adapter_key == "pred":
                    inputs[sig_key] = self.extract_value(pred, "answer", pred)
                else:
                    # Handle custom mappings
                    inputs[sig_key] = kwargs.get(adapter_key, None)
            
            if trace:
                for key, value in inputs.items():
                    print(f"\n{key.capitalize()}: {value}")
            
            # Get the signature class to use
            if self.signature_class:
                signature = self.signature_class
            elif self.signature_name and hasattr(dspy, self.signature_name):
                signature = getattr(dspy, self.signature_name)
            else:
                signature = self.build_custom_signature()
            
            judge = dspy.ChainOfThought(signature)
            
            with dspy.context(lm=self.model):
                result = judge(**inputs)
            
            # Extract scores from result
            scores = []
            for field in self.output_fields:
                if hasattr(result, field):
                    # Extract just the numeric score, removing any extra text
                    score_str = "".join(c for c in str(getattr(result, field)) if c.isdigit() or c == ".")
                    try:
                        score = float(score_str)
                        scores.append(score)
                    except ValueError:
                        if trace:
                            print(f"Could not parse score from {field}: {getattr(result, field)}")
            
            # Calculate final score (average of all output fields)
            if not scores:
                if trace:
                    print("No valid scores found in result")
                return self.normalize_to[0]
            
            raw_score = sum(scores) / len(scores)
            
            # Normalize the score
            final_score = self.normalize_score(raw_score)
            
            if trace:
                print(f"Raw score: {raw_score}")
                print(f"Normalized score: {final_score}")
            
            return final_score
            
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Expected errors when parsing LLM outputs or accessing attributes
            logging.warning(f"Expected error in DSPyMetricAdapter: {str(e)}")
            if trace:
                print(f"\nExpected error in metric evaluation: {str(e)}")
            
            # Return a default score for expected evaluation failures
            return self.normalize_to[0]
            
        except Exception as e:
            # Unexpected errors that might indicate bugs in the code
            logging.error(f"Unexpected error in DSPyMetricAdapter: {str(e)}")
            if trace:
                print(f"\nUnexpected error in metric: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Still return a default score, but this should be investigated
            return self.normalize_to[0]


class ExactMatchMetric(MetricBase):
    """
    Evaluates predictions by checking for exact string matches.
    
    This metric compares the prediction and ground truth strings
    and returns 1.0 if they match exactly, 0.0 otherwise.
    """
    
    def __init__(self, case_sensitive: bool = True, strip_whitespace: bool = True):
        """
        Initialize the exact match metric.
        
        Args:
            case_sensitive: Whether to perform case-sensitive matching
            strip_whitespace: Whether to strip whitespace before comparing
        """
        self.case_sensitive = case_sensitive
        self.strip_whitespace = strip_whitespace
    
    def __call__(
        self, 
        gold: Any, 
        pred: Any, 
        trace: bool = False,
        **kwargs
    ) -> Union[Dict[str, float], float]:
        """
        Check if prediction exactly matches ground truth.
        
        Args:
            gold: Ground truth string or object with a string representation
            pred: Predicted string or object with a string representation
            trace: Whether to print detailed information
            
        Returns:
            Dictionary with 'exact_match' score (1.0 for match, 0.0 for mismatch)
        """
        gold_str = str(gold)
        pred_str = str(pred)
        
        if self.strip_whitespace:
            gold_str = gold_str.strip()
            pred_str = pred_str.strip()
            
        if not self.case_sensitive:
            gold_str = gold_str.lower()
            pred_str = pred_str.lower()
        
        match = 1.0 if gold_str == pred_str else 0.0
        
        if trace:
            print(f"Gold: {gold_str}")
            print(f"Pred: {pred_str}")
            print(f"Match: {match}")
        
        return {"exact_match": match}


def json_evaluation_metric(gold: Any, pred: Any, trace: bool = False) -> Dict[str, float]:
    """
    Evaluates predictions against ground truth using JSON structure comparison.
    
    This function compares the structure and content of JSON objects and
    calculates precision, recall, and F1 scores.
    
    Args:
        gold: Ground truth JSON object or string
        pred: Predicted JSON object or string
        trace: Whether to print detailed information
        
    Returns:
        Dictionary with precision, recall, and F1 scores
    """
    # Parse JSON if needed
    if isinstance(gold, str):
        try:
            gold = json.loads(gold)
        except json.JSONDecodeError:
            if trace:
                print("Error parsing gold JSON")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
            
    if isinstance(pred, str):
        try:
            pred = json.loads(pred)
        except json.JSONDecodeError:
            if trace:
                print("Error parsing pred JSON")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    # Flatten both JSONs
    gold_keys = set(_flatten_keys(gold))
    pred_keys = set(_flatten_keys(pred))
    
    # Calculate metrics
    true_positives = len(gold_keys.intersection(pred_keys))
    false_positives = len(pred_keys - gold_keys)
    false_negatives = len(gold_keys - pred_keys)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    if trace:
        print(f"Gold keys: {gold_keys}")
        print(f"Pred keys: {pred_keys}")
        print(f"Precision: {precision:.2f}")
        print(f"Recall: {recall:.2f}")
        print(f"F1: {f1:.2f}")
    
    return {"precision": precision, "recall": recall, "f1": f1}


def _flatten_keys(obj: Any, prefix: str = "") -> List[str]:
    """
    Recursively flatten a nested dictionary or list into a list of key paths.
    
    Args:
        obj: The object to flatten
        prefix: Current key prefix
        
    Returns:
        List of flattened key paths
    """
    keys = []
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)) and v:  # Only recurse if non-empty
                keys.extend(_flatten_keys(v, key))
            else:
                keys.append(key)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            key = f"{prefix}[{i}]"
            if isinstance(v, (dict, list)) and v:  # Only recurse if non-empty
                keys.extend(_flatten_keys(v, key))
            else:
                keys.append(key)
    else:
        keys.append(prefix)
        
    return keys


class FacilityMetric(MetricBase):
    """
    A specialized metric for evaluating facility categorization predictions.
    
    This metric is based on the evaluation approach in use-cases/facility-support-analyzer/eval.ipynb and
    specifically evaluates JSON predictions with urgency, sentiment, and categories fields.
    """
    
    def __init__(self, 
                 output_field: str = "answer",
                 strict_json: bool = False,
                 **kwargs):
        """
        Initialize the FacilityMetric.
        
        Args:
            output_field: Name of the field containing the ground truth output.
                         This should match the 'golden_output_field' in the adapter config.
            strict_json: Whether to use strict JSON parsing (no code block extraction).
            **kwargs: Additional parameters for customization.
        """
        self.output_field = output_field
        self.strict_json = strict_json
        
    def __call__(self, gold: Any, pred: Any, trace: bool = False, **kwargs) -> Union[Dict[str, float], float]:
        """
        Evaluate a prediction against the ground truth.
        
        Args:
            gold: Ground truth example. Can be a raw value, dictionary, or object
                 with specific attributes
            pred: Predicted example. Can be a raw value, dictionary, or object
            trace: Whether to enable tracing for debugging
            **kwargs: Additional metric-specific parameters
            
        Returns:
            Either a dictionary containing metric scores (if trace=True) or a single float score
        """
        # Extract ground truth using a priority-based approach
        ground_truth = self.extract_value(gold, self.output_field)
        
        # Extract prediction value
        prediction_value = self.extract_value(pred, "answer") or pred
        
        # Get the full evaluation results
        results = self.evaluate(ground_truth, prediction_value, **kwargs)
        
        # Return the full results dictionary if trace is True, otherwise just the total score
        if trace:
            return results
        return float(results.get("total", 0.0))
    
    def extract_value(self, obj: Any, key: str, default: Any = None) -> Any:
        """
        Extract a value from different object types.
        
        Args:
            obj: The object to extract from
            key: The key to extract
            default: Default value if key is not found
            
        Returns:
            The extracted value or default
        """
        # Check for outputs attribute (DSPy Example objects)
        if hasattr(obj, 'outputs') and hasattr(obj.outputs, 'get'):
            value = obj.outputs.get(key)
            if value is not None:
                return value
        
        # Check for direct attribute
        if hasattr(obj, key):
            return getattr(obj, key)
        
        # Check dictionary-like access
        if isinstance(obj, dict) and key in obj:
            return obj[key]
        
        # Check for text attribute (common in Prediction objects)
        if hasattr(obj, 'text'):
            return obj.text
        
        # Fall back to string representation if nothing else works
        if hasattr(obj, '__str__') and not isinstance(obj, (str, bytes, bytearray)):
            return str(obj)
        
        return obj
    
    @staticmethod
    def parse_json(input_string: str):
        """
        Attempts to parse the given string as JSON. If direct parsing fails,
        it tries to extract a JSON snippet from code blocks formatted as:
            ```json
            ... JSON content ...
            ```
        or any code block delimited by triple backticks and then parses that content.

        Parameters:
            input_string (str): The input string which may contain JSON.

        Returns:
            The parsed JSON object.

        Raises:
            ValueError: If parsing fails even after attempting to extract a JSON snippet.
        """
        # Try to parse the string directly.
        try:
            return json.loads(input_string)
        except json.JSONDecodeError as err:
            error = err  # Proceed to try extracting a JSON snippet.

        # Define patterns to search for a JSON code block.
        import re
        patterns = [
            re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE),  # code block with "json" label
            re.compile(r"```(.*?)```", re.DOTALL)  # any code block delimited by triple backticks
        ]
        
        # Attempt extraction using each pattern in order.
        for pattern in patterns:
            match = pattern.search(input_string)
            if match:
                json_candidate = match.group(1).strip()
                try:
                    return json.loads(json_candidate)
                except json.JSONDecodeError:
                    # Continue trying if extraction from the code block didn't result in valid JSON.
                    continue

        # If all attempts fail, raise an error.
        raise error
    
    def evaluate(self, ground_truth: Any, predictions: Any, **kwargs) -> Dict[str, Any]:
        """
        Evaluate a prediction against the ground truth using the approach from use-cases/facility-support-analyzer/eval.ipynb.
        
        Args:
            ground_truth: The ground truth
            predictions: The model's prediction
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with evaluation results
        """
        result = {
            "is_valid_json": False,
            "correct_categories": 0.0,
            "correct_sentiment": False,
            "correct_urgency": False,
        }
        
        try:
            # Parse JSON
            gt = ground_truth if isinstance(ground_truth, dict) else (
                json.loads(ground_truth) if self.strict_json else self.parse_json(ground_truth)
            )
            pred = predictions if isinstance(predictions, dict) else (
                json.loads(predictions) if self.strict_json else self.parse_json(predictions)
            )
        except (json.JSONDecodeError, ValueError):
            # Invalid JSON, return early with default scores
            result["total"] = 0.0
            return result
            
        # Mark as valid JSON
        result["is_valid_json"] = True
        
        # Check if required fields are present
        required_fields = ["categories", "sentiment", "urgency"]
        for field in required_fields:
            if field not in gt or field not in pred:
                result["total"] = 0.0
                return result
        
        # Evaluate categories field
        try:
            # Calculate percentage of correctly matched category boolean values
            result["correct_categories"] = sum(
                [gt["categories"][k] == pred["categories"][k] for k in gt["categories"].keys()]
            ) / len(gt["categories"])
        except (KeyError, TypeError, ZeroDivisionError):
            result["correct_categories"] = 0.0
        
        # Evaluate sentiment field
        result["correct_sentiment"] = pred["sentiment"] == gt["sentiment"]
        
        # Evaluate urgency field
        result["correct_urgency"] = pred["urgency"] == gt["urgency"]
        
        # Calculate total score as average of all correct_* fields
        correct_fields = [v for k, v in result.items() if k.startswith('correct_')]
        result["total"] = sum(correct_fields) / len(correct_fields) if correct_fields else 0.0
        
        return result


class StandardJSONMetric(MetricBase):
    """
    A standardized metric for evaluating JSON predictions against ground truth.
    
    This metric can be configured through YAML to evaluate different aspects of JSON
    predictions, such as field presence, value equality, and structural similarity.
    It supports flexible field mapping and custom scoring logic.
    """
    
    def __init__(self, 
                 output_fields: Optional[Union[List[str], Dict[str, float]]] = None,
                 required_fields: Optional[List[str]] = None,
                 nested_fields: Optional[Dict[str, List[str]]] = None,
                 field_weights: Optional[Dict[str, float]] = None,
                 strict_json: bool = False,
                 evaluation_mode: str = "selected_fields_comparison",
                 output_field: str = "answer",
                 **kwargs):
        """
        Initialize the StandardJSONMetric.
        
        Args:
            output_fields: Fields to evaluate. Can be a list of field names or a dict mapping
                   field names to weights.
            required_fields: Fields that must be present for a valid prediction. If not specified,
                           defaults to the same values as output_fields.
            nested_fields: Nested fields to evaluate, with parent field as key and
                          list of child fields as value.
            field_weights: Weights for each field in the evaluation.
            strict_json: Whether to use strict JSON parsing (no code block extraction).
            evaluation_mode: Mode for evaluation ('selected_fields_comparison' or 'full_json_comparison').
            output_field: Name of the field containing the ground truth output.
                         This should match the 'golden_output_field' in the adapter config.
            **kwargs: Additional parameters for customization.
        """
        # Set up evaluation mode
        self.evaluation_mode = evaluation_mode
        if evaluation_mode not in ["selected_fields_comparison", "full_json_comparison"]:
            raise ValueError(f"Invalid evaluation mode: {evaluation_mode}. Must be 'selected_fields_comparison' or 'full_json_comparison'.")
        
        # Set up fields to evaluate
        if isinstance(output_fields, dict):
            self.fields = list(output_fields.keys())
            self.field_weights = output_fields
        else:
            self.fields = output_fields or []
            self.field_weights = field_weights or {}
            
        # Set default weights for fields not explicitly weighted
        for field in self.fields:
            if field not in self.field_weights:
                self.field_weights[field] = 1.0
                
        # Use fields as the default for required_fields when not specified
        self.required_fields = required_fields if required_fields is not None else self.fields
        self.nested_fields = nested_fields or {}
        self.strict_json = strict_json
        self.output_field = output_field
        
    def __call__(self, gold: Any, pred: Any, trace: bool = False, **kwargs) -> Union[Dict[str, float], float]:
        """
        Evaluate a prediction against the ground truth.
        
        Args:
            gold: Ground truth example. Can be a raw value, dictionary, or object
                 with specific attributes
            pred: Predicted example. Can be a raw value, dictionary, or object
            trace: Whether to enable tracing for debugging
            **kwargs: Additional metric-specific parameters
            
        Returns:
            Either a dictionary containing metric scores (if trace=True) or a single float score
        """
        # Extract ground truth using a priority-based approach
        ground_truth = self.extract_value(gold, self.output_field)
        
        # Extract prediction value
        prediction_value = self.extract_value(pred, "answer") or pred
        
        # Get the full evaluation results
        results = self.evaluate(ground_truth, prediction_value, trace=trace, **kwargs)
        
        # Return the full results dictionary if trace is True, otherwise just the total score
        if trace:
            return results
        return float(results.get("total", 0.0))
        
    def _extract_value(self, obj, field_name):
        """
        Extract a value from an object using a consistent approach.
        
        Args:
            obj: The object to extract from (can be Example, Prediction, dict, etc.)
            field_name: The name of the field to extract
            
        Returns:
            The extracted value or None if not found
        """
        # Check for outputs attribute (DSPy Example objects)
        if hasattr(obj, 'outputs') and hasattr(obj.outputs, 'get'):
            value = obj.outputs.get(field_name)
            if value is not None:
                return value
        
        # Check for direct attribute
        if hasattr(obj, field_name):
            return getattr(obj, field_name)
        
        # Check dictionary-like access
        if isinstance(obj, dict) and field_name in obj:
            return obj[field_name]
        
        # Check for text attribute (common in Prediction objects)
        if hasattr(obj, 'text'):
            return obj.text
        
        # Fall back to string representation if nothing else works
        if hasattr(obj, '__str__') and not isinstance(obj, (str, bytes, bytearray)):
            return str(obj)
        
        return obj
    
    @staticmethod
    def parse_json(input_string: str):
        """
        Attempts to parse the given string as JSON. If direct parsing fails,
        it tries to extract a JSON snippet from code blocks formatted as:
            ```json
            ... JSON content ...
            ```
        or any code block delimited by triple backticks and then parses that content.

        Parameters:
            input_string (str): The input string which may contain JSON.

        Returns:
            The parsed JSON object.

        Raises:
            ValueError: If parsing fails even after attempting to extract a JSON snippet.
        """
        # Try to parse the string directly.
        try:
            return json.loads(input_string)
        except json.JSONDecodeError as err:
            error = err  # Proceed to try extracting a JSON snippet.

        # Define patterns to search for a JSON code block.
        patterns = [
            re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE),  # code block with "json" label
            re.compile(r"```(.*?)```", re.DOTALL)  # any code block delimited by triple backticks
        ]
        
        # Attempt extraction using each pattern in order.
        for pattern in patterns:
            match = pattern.search(input_string)
            if match:
                json_candidate = match.group(1).strip()
                try:
                    return json.loads(json_candidate)
                except json.JSONDecodeError:
                    # Continue trying if extraction from the code block didn't result in valid JSON.
                    continue

        # If all attempts fail, raise an error.
        raise error
    
    def flatten_json(self, json_obj: Any, parent: str = "", sep: str = ".") -> dict:
        """
        Recursively flattens a nested JSON object into a dictionary whose keys are the
        paths to each value in the original JSON.
        
        Args:
            json_obj: The JSON object to flatten
            parent: The parent key (used in recursion)
            sep: The separator to use between nested keys
            
        Returns:
            A flattened dictionary
        """
        items = {}
        if isinstance(json_obj, dict):
            for key, value in json_obj.items():
                new_key = f"{parent}{sep}{key}" if parent else key
                items.update(self.flatten_json(value, new_key, sep=sep))
        elif isinstance(json_obj, list):
            for i, value in enumerate(json_obj):
                new_key = f"{parent}{sep}{i}" if parent else str(i)
                items.update(self.flatten_json(value, new_key, sep=sep))
        else:
            items[parent] = json_obj
        return items
    
    def extract_value(self, obj: Any, key: str, default: Any = None) -> Any:
        """
        Extract a value from different object types.
        
        Args:
            obj: The object to extract from
            key: The key to extract
            default: Default value if key is not found
            
        Returns:
            The extracted value or default
        """
        if hasattr(obj, key):
            return getattr(obj, key)
        elif isinstance(obj, dict) and key in obj:
            return obj[key]
        return default
    
    def evaluate_flattened(self, ground_truth: Any, predictions: Any, **kwargs) -> Dict[str, Any]:
        """
        Evaluate using flattened comparison, similar to DoxMetric.
        
        Args:
            ground_truth: The ground truth
            predictions: The model's prediction
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with evaluation results
        """
        result = {
            "is_valid_json": False,
        }
        
        try:
            # Parse JSON
            gt = ground_truth if isinstance(ground_truth, dict) else (
                json.loads(ground_truth) if self.strict_json else self.parse_json(ground_truth)
            )
            pred = predictions if isinstance(predictions, dict) else (
                json.loads(predictions) if self.strict_json else self.parse_json(predictions)
            )
        except (json.JSONDecodeError, ValueError):
            # Invalid JSON, return early with default scores
            result["total"] = 0.0
            return result
            
        # Mark as valid JSON
        result["is_valid_json"] = True
        
        # Flatten both JSONs
        flattened_gt = self.flatten_json(gt)
        flattened_pred = self.flatten_json(pred)
        
        # Calculate true positives, false positives, and false negatives
        tp = sum(
            1
            for k, v in flattened_gt.items()
            if k in flattened_pred and flattened_pred[k] == v
        )
        fp = sum(1 for k in flattened_pred if k not in flattened_gt)
        fn = sum(1 for k in flattened_gt if k not in flattened_pred)
        
        # Calculate precision and recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        # Calculate the average score
        result["precision"] = precision
        result["recall"] = recall
        result["total"] = (precision + recall) / 2 if (precision + recall) > 0 else 0.0
        
        return result
    
    def evaluate(self, ground_truth: Any, predictions: Any, **kwargs) -> Dict[str, Any]:
        """
        Evaluate a prediction against the ground truth.
        
        Args:
            ground_truth: The ground truth
            predictions: The model's prediction
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with evaluation results
        """
        # Use flattened comparison mode if specified
        if self.evaluation_mode == "full_json_comparison":
            return self.evaluate_flattened(ground_truth, predictions, **kwargs)
            
        # Otherwise use field-based comparison
        """
        Evaluate a prediction against the ground truth.
        
        Args:
            ground_truth: The ground truth
            predictions: The model's prediction
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with evaluation results
        """
        # Initialize result dictionary
        result = {
            "is_valid_json": False,
        }
        
        # Add field-specific results
        for field in self.fields:
            result[f"correct_{field}"] = False
            
        # Add nested field results
        for parent_field, child_fields in self.nested_fields.items():
            for child in child_fields:
                result[f"correct_{parent_field}_{child}"] = False
            
            # Track overall correctness for the parent field
            if child_fields:
                result[f"correct_{parent_field}_overall"] = 0.0
        
        try:
            # Parse JSON
            gt = ground_truth if isinstance(ground_truth, dict) else (
                json.loads(ground_truth) if self.strict_json else self.parse_json(ground_truth)
            )
            pred = predictions if isinstance(predictions, dict) else (
                json.loads(predictions) if self.strict_json else self.parse_json(predictions)
            )
        except (json.JSONDecodeError, ValueError):
            # Invalid JSON, return early with default scores
            result["total"] = 0.0
            return result
            
        # Mark as valid JSON
        result["is_valid_json"] = True
        
        # Check required fields
        missing_required = [field for field in self.required_fields if field not in pred]
        result["has_required_fields"] = len(missing_required) == 0
        
        # Evaluate top-level fields
        for field in self.fields:
            if field in gt and field in pred:
                result[f"correct_{field}"] = gt[field] == pred[field]
                
        # Evaluate nested fields
        for parent_field, child_fields in self.nested_fields.items():
            if parent_field in gt and parent_field in pred:
                correct_children = 0
                for child in child_fields:
                    # Handle nested dictionaries
                    if isinstance(gt[parent_field], dict) and isinstance(pred[parent_field], dict):
                        if child in gt[parent_field] and child in pred[parent_field]:
                            is_correct = gt[parent_field][child] == pred[parent_field][child]
                            result[f"correct_{parent_field}_{child}"] = is_correct
                            if is_correct:
                                correct_children += 1
                                
                # Calculate overall correctness for the parent field
                if child_fields:
                    result[f"correct_{parent_field}_overall"] = correct_children / len(child_fields)
        
        # Calculate total score with weights
        total_weight = 0.0
        weighted_sum = 0.0
        
        # Add top-level field scores
        for field in self.fields:
            key = f"correct_{field}"
            if key in result:
                weight = self.field_weights.get(field, 1.0)
                weighted_sum += float(result[key]) * weight
                total_weight += weight
                
        # Add nested field overall scores
        for parent_field in self.nested_fields:
            key = f"correct_{parent_field}_overall"
            if key in result:
                weight = self.field_weights.get(parent_field, 1.0)
                weighted_sum += result[key] * weight
                total_weight += weight
                
        # Calculate final score
        if total_weight > 0:
            result["total"] = weighted_sum / total_weight
        else:
            result["total"] = 0.0
            
        return result
