# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
import json
from pathlib import Path
from typing import Any, Dict, List, Union

from prompt_ops.core.datasets import DatasetAdapter
from prompt_ops.core.metrics import MetricBase


class FacilityAdapter(DatasetAdapter):
    """
    Custom adapter for facility management datasets with specialized formatting.

    This adapter handles datasets where each example contains a customer message,
    priority level, and categorization information.
    """

    def __init__(self, dataset_path: str, include_metadata: bool = True, **kwargs):
        """
        Initialize the facility adapter.

        Args:
            dataset_path: Path to the dataset file
            include_metadata: Whether to include additional metadata in the output
            **kwargs: Additional configuration parameters
        """
        super().__init__(dataset_path)
        self.include_metadata = include_metadata

    def adapt(self) -> List[Dict[str, Any]]:
        """
        Transform facility dataset format into standardized format.

        Returns:
            List of standardized examples
        """
        # Load the dataset
        with open(self.dataset_path, "r") as f:
            if self.file_format == "json":
                data = json.load(f)
            elif self.file_format == "jsonl":
                data = [json.loads(line) for line in f]
            else:
                raise ValueError(f"Unsupported file format: {self.file_format}")

        standardized_data = []

        for item in data:
            # Extract fields from the dataset
            message = item.get("customer_message", "")
            priority = item.get("priority", "")
            categories = item.get("categories", {})
            sentiment = item.get("sentiment", "")

            # Create standardized example
            example = {
                "inputs": {"question": message},
                "outputs": {
                    "answer": {
                        "urgency": self._map_priority_to_urgency(priority),
                        "sentiment": sentiment,
                        "categories": categories,
                    }
                },
            }

            # Add metadata if requested
            if self.include_metadata:
                example["metadata"] = {
                    "original_priority": priority,
                    "timestamp": item.get("timestamp", ""),
                    "customer_id": item.get("customer_id", ""),
                }

            standardized_data.append(example)

        return standardized_data

    def _map_priority_to_urgency(self, priority: str) -> str:
        """
        Map priority values to standardized urgency levels.

        Args:
            priority: Original priority value

        Returns:
            Standardized urgency level
        """
        priority_map = {
            "critical": "high",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "routine": "low",
        }
        return priority_map.get(priority.lower(), "medium")

    def _infer_format(self, path: Path) -> str:
        """
        Infer the file format from the file extension.

        Args:
            path: Path to the dataset file

        Returns:
            Inferred file format
        """
        suffix = path.suffix.lower()
        if suffix == ".json":
            return "json"
        elif suffix == ".jsonl":
            return "jsonl"
        else:
            raise ValueError(f"Unsupported file extension: {suffix}")


class FacilityMetric(MetricBase):
    """
    Custom metric for evaluating facility management predictions.

    This metric evaluates predictions based on:
    1. Category accuracy
    2. Sentiment accuracy
    3. Urgency accuracy
    """

    def __init__(self, weights: Dict[str, float] = None, **kwargs):
        """
        Initialize the facility metric.

        Args:
            weights: Optional weights for different aspects of the evaluation
            **kwargs: Additional configuration parameters
        """
        self.weights = weights or {"category": 0.5, "sentiment": 0.3, "urgency": 0.2}

    def __call__(
        self, gold: Any, pred: Any, trace: bool = False, **kwargs
    ) -> Union[Dict[str, float], float]:
        """
        Evaluate the prediction against the ground truth.

        Args:
            gold: Ground truth example
            pred: Predicted example (can be a string or dictionary)
            trace: Whether to enable tracing for debugging
            **kwargs: Additional metric-specific parameters

        Returns:
            A score between 0.0 and 1.0 or a dictionary of scores
        """
        # Parse the prediction if it's a string (common with LLM outputs)
        if isinstance(pred, str):
            try:
                pred = json.loads(pred)
            except json.JSONDecodeError:
                # If prediction is not valid JSON, return a low score
                return 0.0

        # Extract the relevant fields from gold
        gold_data = gold.get("answer", gold)

        # Evaluate different aspects
        category_score = self._evaluate_categories(gold_data, pred)
        sentiment_score = self._evaluate_sentiment(gold_data, pred)
        urgency_score = self._evaluate_urgency(gold_data, pred)

        # Combine scores with weights
        total_score = (
            self.weights["category"] * category_score
            + self.weights["sentiment"] * sentiment_score
            + self.weights["urgency"] * urgency_score
        )

        # Return detailed scores if trace is enabled
        if trace:
            return {
                "category": category_score,
                "sentiment": sentiment_score,
                "urgency": urgency_score,
                "overall": total_score,
            }

        return total_score

    def _evaluate_categories(self, gold: Dict[str, Any], pred: Dict[str, Any]) -> float:
        """
        Evaluate category predictions.

        Args:
            gold: Ground truth example
            pred: Predicted example

        Returns:
            A score between 0.0 and 1.0
        """
        gold_categories = gold.get("categories", {})
        pred_categories = pred.get("categories", {})

        # Calculate precision and recall for categories
        correct = 0
        for category, value in pred_categories.items():
            if category in gold_categories and gold_categories[category] == value:
                correct += 1

        precision = correct / len(pred_categories) if pred_categories else 0
        recall = correct / len(gold_categories) if gold_categories else 0

        # Calculate F1 score
        if precision + recall > 0:
            return 2 * precision * recall / (precision + recall)
        return 0.0

    def _evaluate_sentiment(self, gold: Dict[str, Any], pred: Dict[str, Any]) -> float:
        """
        Evaluate sentiment prediction.

        Args:
            gold: Ground truth example
            pred: Predicted example

        Returns:
            A score between 0.0 and 1.0
        """
        gold_sentiment = gold.get("sentiment", "").lower()
        pred_sentiment = pred.get("sentiment", "").lower()

        # Simple exact match for sentiment
        return 1.0 if gold_sentiment == pred_sentiment else 0.0

    def _evaluate_urgency(self, gold: Dict[str, Any], pred: Dict[str, Any]) -> float:
        """
        Evaluate urgency prediction.

        Args:
            gold: Ground truth example
            pred: Predicted example

        Returns:
            A score between 0.0 and 1.0
        """
        gold_urgency = gold.get("urgency", "").lower()
        pred_urgency = pred.get("urgency", "").lower()

        # Simple exact match for urgency
        return 1.0 if gold_urgency == pred_urgency else 0.0
