# Creating Custom Adapters and Metrics in prompt-ops

> **Note:** This tutorial builds on concepts from the [Advanced Facility Configuration Guide](/examples/advanced/advanced_facility_config.md). Make sure you're familiar with the basic configuration options before diving into custom implementations.

## Overview

While prompt-ops provides flexible configuration options through YAML files, there are cases where you might need to create custom adapter and metric classes to handle specialized datasets or evaluation requirements. This tutorial will guide you through:

1. Understanding the base classes for adapters and metrics
2. Creating a custom dataset adapter
3. Creating a custom evaluation metric
4. Registering and using your custom components

## Understanding the Base Classes

### Dataset Adapters

All dataset adapters in prompt-ops inherit from the `DatasetAdapter` base class, which defines the common interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pathlib import Path

class DatasetAdapter(ABC):
    """
    Base adapter class for transforming dataset-specific formats into a standardized format.
    """
    
    def __init__(self, dataset_path: str, file_format: str = None):
        """Initialize the dataset adapter with a path to the dataset file."""
        self.dataset_path = Path(dataset_path)
        self.file_format = file_format or self._infer_format(self.dataset_path)
    
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
        """
        pass
```

### Metrics

All metrics inherit from the `MetricBase` class, which defines the common interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Union, Generic, TypeVar

T = TypeVar('T')  # Type for gold/reference
U = TypeVar('U')  # Type for prediction

class MetricBase(ABC, Generic[T, U]):
    """Base class for all optimization metrics."""
    
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
            gold: Ground truth example
            pred: Predicted example
            trace: Whether to enable tracing for debugging
            **kwargs: Additional metric-specific parameters
            
        Returns:
            Either a dictionary containing metric scores or a single float score
        """
        pass
```

## Creating a Custom Dataset Adapter

Let's create a custom adapter for a facility management dataset that handles a specific format. We'll call it `FacilityCustomAdapter`.

### Step 1: Create a New Module

First, create a new directory for your custom adapter:

```bash
mkdir -p src/prompt_ops/datasets/facility_custom
touch src/prompt_ops/datasets/facility_custom/__init__.py
touch src/prompt_ops/datasets/facility_custom/adapter.py
```

### Step 2: Implement the Adapter

In `src/prompt_ops/datasets/facility_custom/adapter.py`:

```python
"""
Custom adapter for facility management datasets.
"""

from typing import Dict, List, Any
from prompt_ops.core.datasets import DatasetAdapter


class FacilityCustomAdapter(DatasetAdapter):
    """
    Custom adapter for facility management datasets with specialized formatting.
    
    This adapter handles datasets where each example contains a customer message,
    priority level, and categorization information.
    """
    
    def __init__(self, dataset_path: str, include_metadata: bool = True, **kwargs):
        """
        Initialize the facility custom adapter.
        
        Args:
            dataset_path: Path to the dataset file
            include_metadata: Whether to include additional metadata in the output
        """
        super().__init__(dataset_path)
        self.include_metadata = include_metadata
    
    def adapt(self) -> List[Dict[str, Any]]:
        """
        Transform facility dataset format into standardized format.
        
        Returns:
            List of standardized examples
        """
        data = self.load_raw_data()
        standardized_data = []
        
        for item in data:
            # Extract fields from the dataset
            message = item.get("customer_message", "")
            priority = item.get("priority", "")
            categories = item.get("categories", {})
            sentiment = item.get("sentiment", "")
            
            # Create standardized example
            example = {
                "inputs": {
                    "question": message
                },
                "outputs": {
                    "answer": {
                        "urgency": self._map_priority_to_urgency(priority),
                        "sentiment": sentiment,
                        "categories": categories
                    }
                }
            }
            
            # Add metadata if requested
            if self.include_metadata:
                example["metadata"] = {
                    "original_priority": priority,
                    "timestamp": item.get("timestamp", ""),
                    "customer_id": item.get("customer_id", "")
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
            "routine": "low"
        }
        
        return priority_map.get(priority.lower(), "medium")
```

### Step 3: Register the Adapter

In `src/prompt_ops/datasets/facility_custom/__init__.py`:

```python
"""
Custom facility management dataset adapters.
"""

from .adapter import FacilityCustomAdapter

__all__ = ["FacilityCustomAdapter"]
```

## Creating a Custom Metric

Now, let's create a custom metric for evaluating facility management predictions.

### Step 1: Create a New Module

```bash
mkdir -p src/prompt_ops/metrics/facility_custom
touch src/prompt_ops/metrics/facility_custom/__init__.py
touch src/prompt_ops/metrics/facility_custom/metric.py
```

### Step 2: Implement the Metric

In `src/prompt_ops/metrics/facility_custom/metric.py`:

```python
"""
Custom metrics for facility management evaluation.
"""

from typing import Dict, Any, Union, List
import json
from prompt_ops.core.metrics import MetricBase


class FacilityCustomMetric(MetricBase):
    """
    Custom metric for evaluating facility management predictions.
    
    This metric evaluates predictions based on:
    1. Urgency accuracy
    2. Sentiment accuracy
    3. Category matching with partial credit
    """
    
    def __init__(
        self,
        urgency_weight: float = 1.0,
        sentiment_weight: float = 1.0,
        categories_weight: float = 1.5,
        required_categories: List[str] = None,
        strict_json: bool = False
    ):
        """
        Initialize the facility custom metric.
        
        Args:
            urgency_weight: Weight for urgency evaluation
            sentiment_weight: Weight for sentiment evaluation
            categories_weight: Weight for categories evaluation
            required_categories: List of categories that must be present
            strict_json: Whether to use strict JSON parsing
        """
        self.urgency_weight = urgency_weight
        self.sentiment_weight = sentiment_weight
        self.categories_weight = categories_weight
        self.required_categories = required_categories or []
        self.strict_json = strict_json
        
        # Calculate total weight for normalization
        self.total_weight = urgency_weight + sentiment_weight + categories_weight
    
    def __call__(
        self,
        gold: Any,
        pred: Any,
        trace: bool = False,
        **kwargs
    ) -> Union[Dict[str, float], float]:
        """
        Evaluate the prediction against the ground truth.
        
        Args:
            gold: Ground truth example
            pred: Predicted example
            trace: Whether to enable tracing
            
        Returns:
            Dictionary with scores or a single float score
        """
        # Extract values from gold and pred
        gold_data = self._extract_data(gold)
        pred_data = self._extract_data(pred)
        
        if gold_data is None or pred_data is None:
            if trace:
                print("Failed to parse gold or pred as JSON")
            return 0.0
        
        # Evaluate individual components
        urgency_score = self._evaluate_urgency(gold_data, pred_data)
        sentiment_score = self._evaluate_sentiment(gold_data, pred_data)
        categories_score = self._evaluate_categories(gold_data, pred_data)
        
        # Calculate weighted score
        weighted_score = (
            (urgency_score * self.urgency_weight) +
            (sentiment_score * self.sentiment_weight) +
            (categories_score * self.categories_weight)
        ) / self.total_weight
        
        if trace:
            return {
                "urgency": urgency_score,
                "sentiment": sentiment_score,
                "categories": categories_score,
                "overall": weighted_score
            }
        
        return weighted_score
    
    def _extract_data(self, data: Any) -> Dict[str, Any]:
        """
        Extract data from various formats.
        
        Args:
            data: Input data (could be string, dict, or object)
            
        Returns:
            Extracted data as dictionary
        """
        if isinstance(data, dict):
            # Check if this is a standardized example
            if "outputs" in data and "answer" in data["outputs"]:
                return data["outputs"]["answer"]
            if "answer" in data:
                return data["answer"]
            return data
        
        if isinstance(data, str):
            # Try to parse as JSON
            if not self.strict_json:
                # Extract JSON from markdown code blocks if present
                if "```json" in data:
                    start = data.find("```json") + 7
                    end = data.find("```", start)
                    if end > start:
                        data = data[start:end].strip()
                elif "```" in data:
                    start = data.find("```") + 3
                    end = data.find("```", start)
                    if end > start:
                        data = data[start:end].strip()
            
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        
        return None
    
    def _evaluate_urgency(self, gold: Dict[str, Any], pred: Dict[str, Any]) -> float:
        """
        Evaluate urgency prediction.
        
        Args:
            gold: Ground truth data
            pred: Predicted data
            
        Returns:
            Score between 0.0 and 1.0
        """
        gold_urgency = str(gold.get("urgency", "")).lower()
        pred_urgency = str(pred.get("urgency", "")).lower()
        
        return 1.0 if gold_urgency == pred_urgency else 0.0
    
    def _evaluate_sentiment(self, gold: Dict[str, Any], pred: Dict[str, Any]) -> float:
        """
        Evaluate sentiment prediction.
        
        Args:
            gold: Ground truth data
            pred: Predicted data
            
        Returns:
            Score between 0.0 and 1.0
        """
        gold_sentiment = str(gold.get("sentiment", "")).lower()
        pred_sentiment = str(pred.get("sentiment", "")).lower()
        
        return 1.0 if gold_sentiment == pred_sentiment else 0.0
    
    def _evaluate_categories(self, gold: Dict[str, Any], pred: Dict[str, Any]) -> float:
        """
        Evaluate category predictions with partial credit.
        
        Args:
            gold: Ground truth data
            pred: Predicted data
            
        Returns:
            Score between 0.0 and 1.0
        """
        gold_categories = gold.get("categories", {})
        pred_categories = pred.get("categories", {})
        
        if not isinstance(gold_categories, dict) or not isinstance(pred_categories, dict):
            return 0.0
        
        # Check required categories
        for category in self.required_categories:
            if category not in pred_categories:
                return 0.0
        
        # Calculate true positives, false positives, and false negatives
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        for category, value in gold_categories.items():
            if category in pred_categories:
                if bool(value) == bool(pred_categories[category]):
                    true_positives += 1
                else:
                    false_positives += 1
            elif bool(value):
                false_negatives += 1
        
        for category, value in pred_categories.items():
            if category not in gold_categories and bool(value):
                false_positives += 1
        
        # Calculate F1 score
        if true_positives + false_positives + false_negatives == 0:
            return 1.0  # Perfect match if both are empty
        
        if true_positives == 0:
            return 0.0  # No matches
        
        precision = true_positives / (true_positives + false_positives)
        recall = true_positives / (true_positives + false_negatives)
        
        f1 = 2 * (precision * recall) / (precision + recall)
        return f1
```

### Step 3: Register the Metric

In `src/prompt_ops/metrics/facility_custom/__init__.py`:

```python
"""
Custom facility management metrics.
"""

from .metric import FacilityCustomMetric

__all__ = ["FacilityCustomMetric"]
```

## Using Custom Components in YAML Configuration

Now that you've created custom adapter and metric classes, you can use them in your YAML configuration:

```yaml
# Model Configuration
model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"
  api_base: "https://openrouter.ai/api/v1"
  temperature: 0.0

# Dataset Configuration with Custom Adapter
dataset:
  adapter_class: "prompt_ops.datasets.facility_custom.FacilityCustomAdapter"
  path: "../dataset/facility-synth/facility_custom.json"
  include_metadata: true
  train_size: 0.7
  validation_size: 0.15

# Prompt Configuration
prompt:
  file: "../dataset/facility-synth/facility_prompt_sys.txt"
  inputs: ["question"]
  outputs: ["answer"]

# Metric Configuration with Custom Metric
metric:
  class: "prompt_ops.metrics.facility_custom.FacilityCustomMetric"
  urgency_weight: 1.0
  sentiment_weight: 1.0
  categories_weight: 1.5
  required_categories: ["emergency_repair_services", "routine_maintenance_requests"]
  strict_json: false

# Optimization Settings
optimization:
  strategy: "light"
  max_rounds: 3
  max_examples_per_round: 5
  max_prompt_length: 2048
```

## Best Practices for Custom Components

When creating custom adapters and metrics, follow these best practices:

1. **Maintain the Interface**: Always inherit from the base classes and implement all required methods.

2. **Handle Edge Cases**: Your code should gracefully handle missing fields, malformed data, and unexpected inputs.

3. **Add Documentation**: Include detailed docstrings explaining what your component does and how to use it.

4. **Use Type Hints**: Add proper type annotations to make your code more maintainable.

5. **Keep It Modular**: Break down complex logic into helper methods for better readability and testability.

6. **Test Thoroughly**: Create unit tests for your custom components to ensure they work as expected.

## Conclusion

Creating custom adapters and metrics allows you to tailor prompt-ops to your specific needs. By following the patterns established in the base classes, you can seamlessly integrate your custom components with the rest of the framework.

## Next Steps

- Contribute your custom components back to the prompt-ops project
