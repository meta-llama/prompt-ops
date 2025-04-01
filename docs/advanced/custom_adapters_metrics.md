# Creating Custom Adapters and Metrics in prompt-ops

> **Note:** This guide explains how to create custom dataset adapters and evaluation metrics for specialized use cases in prompt-ops.

## Overview

While prompt-ops provides built-in adapters and metrics for common scenarios, you may need to handle specialized datasets or evaluation requirements. This guide explains how to create two essential classes in a simple Python file:

1. A custom `DatasetAdapter` class - Transforms your custom data format into the standardized format
2. A custom `MetricBase` class - Evaluates predictions against ground truth

## Creating Custom Adapters and Metrics

You can create both custom adapters and metrics in a single Python file that can be referenced in your YAML configuration.

### Basic Structure

Create a Python file (e.g., `my_custom_adapters.py`) with the following structure:

```python
from typing import Dict, List, Any, Union
from pathlib import Path
from prompt_ops.core.datasets import DatasetAdapter
from prompt_ops.core.metrics import MetricBase

class MyCustomAdapter(DatasetAdapter):
    """
    Custom adapter for transforming dataset-specific formats into a standardized format.
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        Initialize the dataset adapter with a path to the dataset file.
        
        Args:
            dataset_path: Path to the dataset file
            **kwargs: Additional configuration parameters from your YAML config
        """
        super().__init__(dataset_path)
        # Initialize any custom parameters here
        
    def adapt(self) -> List[Dict[str, Any]]:
        """
        Transform dataset-specific format into standardized format.
        
        Returns:
            List of standardized examples in the format:
            [
                {
                    "inputs": {"question": "Your input text here"},
                    "outputs": {"answer": "Expected output here"},
                    "metadata": {"optional": "metadata"}  # Optional
                },
                ...
            ]
        """
        # Your implementation here
        pass

class MyCustomMetric(MetricBase):
    """
    Custom metric for evaluating predictions.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the metric with custom parameters.
        
        Args:
            **kwargs: Configuration parameters from your YAML config
        """
        # Initialize any custom parameters here
        
    def __call__(self, gold: Any, pred: Any, trace: bool = False, **kwargs) -> Union[Dict[str, float], float]:
        """
        Evaluate a prediction against the ground truth.
        
        Args:
            gold: Ground truth example
            pred: Model prediction to evaluate
            trace: Whether to return detailed scores
            **kwargs: Additional parameters
            
        Returns:
            A score between 0.0 and 1.0 or a dictionary of scores
        """
        # Your implementation here
        pass
```

## Example Implementation

Here's a complete example of custom adapter and metric classes for a facility management dataset:

```python
import json
from typing import Dict, List, Any, Union
from pathlib import Path
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
        with open(self.dataset_path, 'r') as f:
            if self.file_format == 'json':
                data = json.load(f)
            elif self.file_format == 'jsonl':
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
    
    def _infer_format(self, path: Path) -> str:
        """
        Infer the file format from the file extension.
        
        Args:
            path: Path to the dataset file
            
        Returns:
            Inferred file format
        """
        suffix = path.suffix.lower()
        if suffix == '.json':
            return 'json'
        elif suffix == '.jsonl':
            return 'jsonl'
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
        self.weights = weights or {
            "category": 0.5,
            "sentiment": 0.3,
            "urgency": 0.2
        }
    
    def __call__(self, gold: Any, pred: Any, trace: bool = False, **kwargs) -> Union[Dict[str, float], float]:
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
            self.weights["category"] * category_score +
            self.weights["sentiment"] * sentiment_score +
            self.weights["urgency"] * urgency_score
        )
        
        # Return detailed scores if trace is enabled
        if trace:
            return {
                "category": category_score,
                "sentiment": sentiment_score,
                "urgency": urgency_score,
                "overall": total_score
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
```

## Using Your Custom Classes in YAML Configuration

Once you've created your custom adapter and metric classes, you can use them in your YAML configuration by specifying the module path:

```yaml
dataset:
  adapter_class: "path.to.module.FacilityAdapter"
  path: "/path/to/dataset.json"
  adapter_params:
    include_metadata: true

metric:
  metric_class: "path.to.module.FacilityMetric"
  metric_params:
    weights:
      category: 0.5
      sentiment: 0.3
      urgency: 0.2
```

## Best Practices for Custom Adapters and Metrics

1. **Input/Output Standardization**: Always normalize your dataset to use consistent field names:
   - Use `"question"` for the main input field
   - Use `"answer"` for the main output field

2. **Error Handling**: Include robust error handling in your evaluation method to handle:
   - Malformed predictions (e.g., non-JSON strings)
   - Missing fields in predictions
   - Type mismatches between gold and prediction

3. **Documentation**: Document your classes with clear docstrings explaining:
   - Expected input format
   - Output format
   - Any special handling or transformations

4. **Testing**: Test your adapter and metric with sample data before using them in a full optimization run:
   ```python
   # Test your adapter
   adapter = FacilityAdapter("/path/to/test_data.json")
   examples = adapter.adapt()
   print(f"Processed {len(examples)} examples")
   print(examples[0])  # Check the first example
   
   # Test your metric
   metric = FacilityMetric()
   gold = examples[0]["outputs"]["answer"]
   pred = {"sentiment": "positive", "urgency": "high", "categories": {"maintenance": True}}
   score = metric(gold, pred)
   print(f"Evaluation score: {score}")
   ```

## Advanced Example: Handling Complex JSON Structures

For datasets with complex nested structures, you may need more sophisticated parsing in your adapter class:

```python
class ComplexJSONAdapter(DatasetAdapter):
    """Adapter for complex nested JSON structures."""
    
    def __init__(self, dataset_path: str, input_path: List[str] = None, output_path: List[str] = None, **kwargs):
        """
        Initialize the complex JSON adapter.
        
        Args:
            dataset_path: Path to the dataset file
            input_path: List of keys to navigate to the input field
            output_path: List of keys to navigate to the output field
            **kwargs: Additional configuration parameters
        """
        super().__init__(dataset_path)
        self.input_path = input_path or ["content", "message", "text"]
        self.output_path = output_path or ["annotations", "labels"]
    
    def adapt(self) -> List[Dict[str, Any]]:
        """Transform complex JSON format into standardized format."""
        with open(self.dataset_path, 'r') as f:
            data = json.load(f)
        
        standardized_data = []
        
        # Handle nested data structures
        for item in data.get("records", []):
            # Extract nested fields using helper function
            input_text = self._extract_nested_field(item, self.input_path)
            output_data = self._extract_nested_field(item, self.output_path)
            
            if input_text is not None and output_data is not None:
                example = {
                    "inputs": {"question": input_text},
                    "outputs": {"answer": output_data}
                }
                standardized_data.append(example)
        
        return standardized_data
    
    def _extract_nested_field(self, data: Dict[str, Any], path: List[str]) -> Any:
        """Extract a value from a nested dictionary using a path of keys."""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
```

## Conclusion

Creating custom adapter and metric classes for prompt-ops allows you to work with specialized datasets and evaluation requirements while maintaining a clean, object-oriented approach. By implementing these classes in a simple Python file, you can:

1. Transform your custom data formats into the standardized format required by prompt-ops
2. Create specialized evaluation metrics tailored to your specific use case
3. Integrate seamlessly with the prompt-ops configuration system

This approach provides a flexible way to extend prompt-ops functionality without modifying the core codebase, allowing you to leverage the optimization framework while accommodating your unique requirements.