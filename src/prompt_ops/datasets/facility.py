"""
Facility dataset adapter for the prompt-migrator.

This module provides an adapter for the facility dataset for customer service messages.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union


class FacilityMetric:
    """
    Evaluation metric for the facility dataset.
    
    This metric evaluates the quality of predictions for the facility dataset
    by comparing the predicted JSON with the ground truth.
    """
    
    def __init__(self, **kwargs):
        """Initialize the facility metric."""
        self.name = "facility_metric"
        
    def __call__(self, example, prediction, **kwargs) -> Dict[str, Any]:
        """
        Evaluate a prediction against the ground truth.
        
        Args:
            example: The example with ground truth
            prediction: The model's prediction
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with evaluation results
        """
        ground_truth = example.outputs.get("answer", "")
        return self.evaluate(ground_truth, prediction, **kwargs)
    
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

    def evaluate(self, ground_truth: Any, predictions: Any, strict_json: bool = True) -> Dict[str, Any]:
        """
        Evaluate a prediction against the ground truth.
        
        Args:
            ground_truth: The ground truth
            predictions: The model's prediction
            strict_json: Whether to use strict JSON parsing
            
        Returns:
            Dictionary with evaluation results
        """
        result = {
            "is_valid_json": False,
            "correct_categories": 0.,
            "correct_sentiment": False,
            "correct_urgency": False,
        }
        try:
            ground_truth = ground_truth if isinstance(ground_truth, dict) else (
                json.loads(ground_truth) if strict_json else self.parse_json(ground_truth)
            )
            predictions = predictions if isinstance(predictions, dict) else (
                json.loads(predictions) if strict_json else self.parse_json(predictions)
            )
        except (json.JSONDecodeError, ValueError):
            pass
        else:
            result["is_valid_json"] = True
            result["correct_categories"] = sum([
                ground_truth["categories"][k] == predictions["categories"][k] 
                for k in ground_truth["categories"].keys()
            ]) / len(ground_truth["categories"])
            result["correct_sentiment"] = predictions["sentiment"] == ground_truth["sentiment"]
            result["correct_urgency"] = predictions["urgency"] == ground_truth["urgency"]
        
        result["total"] = sum([
            float(v) for k, v in result.items() if k.startswith('correct_')
        ]) / len([k for k in result.keys() if k.startswith('correct')])
        
        return result
