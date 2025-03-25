"""
Metrics for evaluating prompt optimization performance.

This module contains the base metric class and various implementations
for evaluating the quality of optimized prompts.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List, Callable, TypeVar, Generic, Type, get_type_hints
import dspy


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
            
        except Exception as e:
            if trace:
                print(f"\nError in metric: {str(e)}")
            
            # Return a default score if evaluation fails
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


class LLMAsJudgeMetric(MetricBase):
    """
    Uses an LLM to evaluate the quality of optimized prompts.
    
    This metric sends both the original and optimized prompts to an LLM
    and asks it to judge the quality of the optimization.
    """
    
    def __init__(self, model_name: str = "llama-3", criteria: Optional[List[str]] = None):
        """
        Initialize the LLM-as-judge metric.
        
        Args:
            model_name: Name of the LLM to use for evaluation
            criteria: List of criteria to evaluate (e.g., clarity, specificity)
        """
        self.model_name = model_name
        self.criteria = criteria or ["clarity", "specificity", "effectiveness"]
    
    def __call__(
        self, 
        gold: Any, 
        pred: Any, 
        trace: bool = False,
        **kwargs
    ) -> Union[Dict[str, float], float]:
        """
        Use an LLM to evaluate the optimization quality.
        
        Args:
            gold: Original prompt
            pred: Optimized prompt
            trace: Whether to print detailed information
            
        Returns:
            Dictionary with scores for each evaluation criterion
        """
        # TODO
        
        # For now, return dummy scores
        scores = {criterion: 0.8 for criterion in self.criteria}
        scores["overall"] = sum(scores.values()) / len(scores)
        
        if trace:
            print(f"Original prompt: {gold}")
            print(f"Optimized prompt: {pred}")
            print(f"Evaluation scores: {scores}")
        
        return scores


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
        for key, value in obj.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (dict, list)) and value:  # Non-empty container
                keys.extend(_flatten_keys(value, new_key))
            else:
                keys.append(new_key)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            new_key = f"{prefix}[{i}]"
            if isinstance(value, (dict, list)) and value:  # Non-empty container
                keys.extend(_flatten_keys(value, new_key))
            else:
                keys.append(new_key)
    else:
        keys.append(prefix)
        
    return keys
