# Using llama-prompt-ops for your use case (with Examples)

> **Note:** This guide explains how to add new use cases to llama-prompt-ops by either configuring existing components or creating custom components.

## Overview

When adding your use case to llama-prompt-ops, you'll need to handle two key aspects:

1. **Dataset Processing** - Converting your data into the standardized format that llama-prompt-ops can work with
2. **Evaluation** - Measuring how well model outputs match expected results

For each aspect, you have two options:

- **Use existing dataset adapter and metric** with configuration - Simpler and recommended for most cases
- **Create custom dataset adapter and metric** - For specialized requirements that can't be handled by existing dataset adapter and metric components

## Dataset Processing: Two Approaches

### Option 1: Use an Existing DatasetAdapter

You can use the built-in dataset adapter, if your dataset follows the following dataset format:

#### Available Adapters

| Adapter Type | Dataset Format | When to Use |
|--------------|----------------|-------------|
| **StandardJSONAdapter** | `[{"question": "What is X?", "answer": "Y"}]` | For most common datasets with simple input/output pairs |
| **RAGJSONAdapter** | `[{"question": "...", "context": "...", "answer": "..."}]` | When your dataset includes retrieval contexts |

See our [detailed adapter selection guide](../dataset_adapter_selection_guide.md) for more information. For many datasets, you can use built-in datasetAdapters. with custom configuration in your YAML file: 

```yaml
dataset:
  adapter_class: "prompt_ops.core.datasets.StandardJSONAdapter"
  path: "/path/to/dataset.json"
  adapter_params:
    input_field: "question"  # or ["nested", "field", "path"]
    output_field: "answer"   # or custom field name
```


### Option 2: Create a Custom Adapter

Create a custom adapter when your dataset requires specialized processing that can't be handled by existing adapters.

#### When to Create a Custom Adapter

Create a custom adapter when:

1. **Complex Structure** - Your dataset has a nested or non-standard format
2. **Special Processing** - You need domain-specific preprocessing or normalization
3. **Multiple Sources** - You're combining data from multiple files or sources
4. **Custom Validation** - You need to validate or filter examples based on specific rules

See the section below on [Implementing Custom Components](#implementing-custom-components) for examples of how to create custom dataset adapters.

## Evaluation Metric: Two Approaches

### Option 1: Use an Existing Metric

You can use the built-in metric, if your metric follows the following metric format:


#### Available Metrics

| Metric Type | Use Case | Expected Format | When to Use |
|-------------|----------|-----------------|-------------|
| **ExactMatchMetric** | Simple text matching | Plain text | For exact string comparison between prediction and ground truth |
| **StandardJSONMetric** | Structured evaluation | JSON objects | For comparing specific fields in structured JSON responses |


See our [detailed metric selection guide](metric_selection_guide.md) for more information. For common evaluation needs, use a built-in metric with custom configuration:

```yaml
metric:
  class: "prompt_ops.core.metrics.StandardJSONMetric"
  params:
    output_fields: ["categories", "sentiment"]
    required_fields: ["categories"]
```

### Option 2: Create a Custom Metric

Create a custom metric when you need specialized evaluation logic that can't be handled by existing metrics.

#### When to Create a Custom Metric

Create a custom metric when:

1. **Domain-Specific Scoring** - You need specialized scoring rules for your domain
2. **Complex Evaluation** - Your evaluation requires multi-step or multi-aspect assessment
3. **Custom Parsing** - You need special parsing of model outputs
4. **Specialized Output Format** - Your model outputs in a format not supported by existing metrics

See the section below on [Implementing Custom Components](#implementing-custom-components) for examples of how to create custom dataset adapters.

---

## Implementing Custom Components

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

### Standardized Format

The `DatasetAdapter.adapt()` method transforms your custom dataset into a standardized format that llama-prompt-ops can work with. This standardized format is a list of dictionaries, where each dictionary represents a single example with the following structure:

```python
{
    "inputs": {
        # Input fields that will be passed to the model
        "question": "Your input text here",  # Required - the main input text
        # Additional input fields can be included if needed
    },
    "outputs": {
        # Expected output fields for evaluation
        "answer": "Expected output here",  # Required - the expected response
        # Can be a string or structured data (dict, list, etc.)
    },
    "metadata": {  # Optional
        # Any additional information about the example
        "id": "example-123",
        "source": "training-set",
        # Any other metadata fields
    }
}
```

The standardized format enables llama-prompt-ops to:

1. Format inputs consistently for different models
2. Compare model outputs against expected outputs
3. Track additional information through the metadata field


## Real-World Example: Customer Service Classification

Let's walk through a complete example of adding a customer service classification use case to llama-prompt-ops.

### Step 1: Analyze Your Dataset

First, examine your dataset structure to determine if you need a custom adapter:

```json
[
  {
    "customer_message": "The heating in my apartment isn't working and it's freezing!",
    "priority": "high",
    "categories": {"maintenance": true, "heating": true},
    "sentiment": "negative"
  },
  ...
]
```

### Step 2: Decide on Your Approach

For this example, we have two options:

**Option A: Use StandardJSONAdapter with configuration**
```yaml
dataset:
  adapter_class: "prompt_ops.core.datasets.StandardJSONAdapter"
  path: "/path/to/customer_service.json"
  adapter_params:
    input_field: "customer_message"
    output_field: {"urgency": "priority", "categories": "categories", "sentiment": "sentiment"}
```

**Option B: Create a custom adapter for more control**

Let's implement a custom adapter for this example:

```python
# customer_service.py
import json
from typing import Dict, List, Any
from prompt_ops.core.datasets import DatasetAdapter
from prompt_ops.core.metrics import MetricBase

class CustomerServiceAdapter(DatasetAdapter):
    """Adapter for customer service datasets."""

    def __init__(self, dataset_path: str, **kwargs):
        super().__init__(dataset_path)
        # Any custom initialization

    def adapt(self) -> List[Dict[str, Any]]:
        """Transform customer service data into standardized format."""
        with open(self.dataset_path, 'r') as f:
            data = json.load(f)

        standardized_data = []
        for item in data:
            # Map priority to standardized urgency levels
            urgency = self._map_priority(item.get("priority", ""))
            
            example = {
                "inputs": {
                    "question": item.get("customer_message", "")
                },
                "outputs": {
                    "answer": {
                        "urgency": urgency,
                        "categories": item.get("categories", {}),
                        "sentiment": item.get("sentiment", "")
                    }
                }
            }
            standardized_data.append(example)

        return standardized_data

    def _map_priority(self, priority: str) -> str:
        """Map priority values to standardized urgency levels."""
        priority_map = {
            "critical": "high",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        return priority_map.get(priority.lower(), "medium")


class CustomerServiceMetric(MetricBase):
    """Metric for evaluating customer service predictions."""

    def __init__(self, weights: Dict[str, float] = None, **kwargs):
        self.weights = weights or {
            "categories": 0.5,
            "sentiment": 0.3,
            "urgency": 0.2
        }

    def __call__(self, gold: Any, pred: Any, trace: bool = False, **kwargs):
        """Evaluate the prediction against the ground truth."""
        # Parse prediction if it's a string
        if isinstance(pred, str):
            try:
                pred = json.loads(pred)
            except json.JSONDecodeError:
                return 0.0

        # Extract gold data
        gold_data = gold.get("answer", gold)

        # Calculate individual scores
        category_score = self._evaluate_categories(gold_data, pred)
        sentiment_score = self._evaluate_sentiment(gold_data, pred)
        urgency_score = self._evaluate_urgency(gold_data, pred)

        # Calculate weighted score
        total_score = (
            self.weights["categories"] * category_score +
            self.weights["sentiment"] * sentiment_score +
            self.weights["urgency"] * urgency_score
        )

        if trace:
            return {
                "categories": category_score,
                "sentiment": sentiment_score,
                "urgency": urgency_score,
                "overall": total_score
            }

        return total_score

    def _evaluate_categories(self, gold, pred):
        """Evaluate category predictions using F1 score."""
        # Implementation details omitted for brevity
        return 1.0  # Placeholder

    def _evaluate_sentiment(self, gold, pred):
        """Evaluate sentiment prediction."""
        # Implementation details omitted for brevity
        return 1.0  # Placeholder

    def _evaluate_urgency(self, gold, pred):
        """Evaluate urgency prediction."""
        # Implementation details omitted for brevity
        return 1.0  # Placeholder
```

### Step 3: Create Your Configuration File

```yaml
# customer_service_config.yaml
dataset:
  adapter_class: "path.to.your.module.CustomerServiceAdapter"
  path: "/path/to/customer_service.json"

metric:
  class: "path.to.your.module.CustomerServiceMetric"
  params:
    weights:
      categories: 0.5
      sentiment: 0.3
      urgency: 0.2

model:
  provider: "openrouter"
  name: "meta-llama/llama-3-70b-instruct"

prompt:
  template: |
    Analyze the following customer service message and provide:
    1. Urgency level (high, medium, or low)
    2. Sentiment (positive, negative, or neutral)
    3. Categories that apply (maintenance, billing, etc.)

    Message: {{question}}

    Respond in JSON format with the following structure:
    {"urgency": "...", "sentiment": "...", "categories": {"category1": true, ...}}
```

### Step 4: Run llama-prompt-ops

```bash
# Set your API key
export OPENROUTER_API_KEY=your_key_here

# Run llama-prompt-ops with your configuration
llama-prompt-ops migrate --config path/to/customer_service_config.yaml
```

## Conclusion

When adding a new use case to llama-prompt-ops, you have two approaches:

1. **Configure existing components** - Simpler and sufficient for most common use cases
2. **Create custom components** - For specialized requirements that need custom processing

Happy Prompt Engineering!