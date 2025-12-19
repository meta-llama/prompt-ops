---
title: Metric Selection Guide
category: Guides
description: Choose the right evaluation metrics for your optimization use case
order: 10
icon: settings
---

# Metric Selection Guide

This guide helps you choose the right evaluation metric for your use case or determine when to create a custom metric.

## Metric Comparison Matrix

| Metric Type | Use Case | Expected Format | When to Use |
|-------------|----------|-----------------|-------------|
| **ExactMatchMetric** | Simple string matching | Plain text strings | When you need exact string matching between prediction and ground truth |
| **StandardJSONMetric** | Structured JSON evaluation | JSON objects or strings | When evaluating structured JSON responses with specific fields to compare |
| **Custom Metric** | Specialized evaluation needs | Any custom format | When existing metrics don't meet your evaluation needs |

## When to Create a Custom Metric

Create a custom metric when:

1. **Complex Evaluation Logic**: Your evaluation requires complex logic that can't be handled by configuring existing metrics
2. **Domain-Specific Scoring**: You need domain-specific scoring rules or normalization
3. **Multi-Step Evaluation**: Your evaluation process involves multiple steps or comparisons
4. **Custom Parsing**: You need special parsing logic for your predictions or ground truth
5. **Specialized Output Format**: Your model outputs in a format not supported by existing metrics

## Custom Metric Implementation Example

```python
from prompt_ops.core.metrics import MetricBase

class MyCustomMetric(MetricBase):
    def __init__(self, custom_param=None, **kwargs):
        # Initialize any custom parameters
        self.custom_param = custom_param

    def __call__(self, gold, pred, trace=False, **kwargs):
        """
        Evaluate the prediction against the ground truth.

        Args:
            gold: Ground truth example
            pred: Predicted example
            trace: Whether to enable tracing for debugging

        Returns:
            Either a dictionary containing metric scores or a single float score
        """
        # Extract values from gold and pred
        gold_value = self.extract_value(gold, "answer", gold)
        pred_value = self.extract_value(pred, "answer", pred)

        # Your custom evaluation logic here
        score = self._calculate_score(gold_value, pred_value)

        if trace:
            # Return detailed results for debugging
            return {
                "score": score,
                "details": {
                    "gold": gold_value,
                    "pred": pred_value,
                    # Add any other details
                }
            }

        # Return a single score for normal use
        return score

    def _calculate_score(self, gold, pred):
        # Implement your custom scoring logic here
        # Return a float score between 0.0 and 1.0
        pass
```

## Configuration Examples

### ExactMatchMetric Configuration

```yaml
metric:
  class: "prompt_ops.core.metrics.ExactMatchMetric"
  params:
    case_sensitive: false
    strip_whitespace: true
```

### StandardJSONMetric Configuration

```yaml
metric:
  class: "prompt_ops.core.metrics.StandardJSONMetric"
  params:
    output_fields: ["categories", "sentiment", "urgency"]
    required_fields: ["categories"]
    nested_fields:
      categories: ["cleaning_services", "maintenance", "security"]
    field_weights:
      categories: 0.6
      sentiment: 0.2
      urgency: 0.2
    evaluation_mode: "selected_fields_comparison"
```

### FacilityMetric Configuration

```yaml
metric:
  class: "prompt_ops.core.metrics.FacilityMetric"
  params:
    output_field: "answer"
    strict_json: false
```

## Example Metrics Implementation

For more complex evaluation needs, you can implement specialized metrics. For example:

- The [HotpotQA Metric](src/prompt_ops/datasets/hotpotqa/metric.py) shows how to implement specialized evaluation for multi-hop question answering, handling answer correctness and supporting fact verification.
