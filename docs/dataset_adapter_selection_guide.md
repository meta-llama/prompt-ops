# Dataset Adapter Selection Guide

This guide helps you choose the right dataset adapter for your use case or determine when to create a custom adapter.

## Dataset Adapter Comparison Matrix

| Adapter Type | Use Case | Dataset Structure | When to Use |
|--------------|----------|-------------------|-------------|
| **StandardJSONAdapter** | General purpose JSON processing | `[{"question": "...", "answer": "..."}]`  | When your dataset has a simple structure with input/output pairs that can be mapped with configuration |
| **RAGJSONAdapter** | Retrieval-augmented generation | `[{"question": "...", "context": "...", "answer": "..."}]` | When your dataset includes retrieval contexts or documents alongside questions and answers |
| **Custom DatasetAdapter** | Specialized formats or processing | Any custom structure | When existing adapters don't meet your needs even with configuration |

## When to Create a Custom DatasetAdapter

Create a custom dataset adapter when:

1. **Complex Structure**: Your dataset has a complex structure that can't be handled by configuring existing adapters
2. **Special Processing**: You need special processing logic beyond simple field extraction and transformation
3. **Domain-Specific Logic**: Your domain requires specific validation, normalization, or enrichment
4. **Multiple Data Sources**: You need to combine or join data from multiple sources

## Custom DatasetAdapter Implementation Example

```python
from prompt_ops.core.datasets import DatasetAdapter

class MyCustomAdapter(DatasetAdapter):
    def __init__(self, dataset_path, **kwargs):
        super().__init__(dataset_path)
        # Initialize any custom parameters
        self.special_param = kwargs.get('special_param')
        
    def adapt(self):
        # Load raw data
        raw_data = self.load_raw_data()
        
        # Transform into standardized format
        standardized_data = []
        for item in raw_data:
            # Your custom transformation logic here
            # This is where you can implement any special processing
            
            standardized_example = {
                "inputs": {
                    "question": self._process_question(item),
                    # Add any other input fields
                },
                "outputs": {
                    "answer": self._process_answer(item),
                    # Add any other output fields
                },
                "metadata": self._extract_metadata(item)
            }
            standardized_data.append(standardized_example)
        
        return standardized_data
    
    def _process_question(self, item):
        # Custom question processing logic
        pass
    
    def _process_answer(self, item):
        # Custom answer processing logic
        pass
    
    def _extract_metadata(self, item):
        # Extract any relevant metadata
        return {}
```

## Decision Flowchart for DatasetAdapter Selection

1. **Is your dataset in JSON format?**
   - **Yes**: Continue to next question
   - **No**: Is it CSV or YAML? Use StandardJSONAdapter with appropriate file_format parameter

2. **Does your dataset have question, context, and answer fields?**
   - **Yes**: Use RAGJSONAdapter
   - **No**: Continue to next question

3. **Is your dataset for customer service categorization?**
   - **Yes**: Use FacilityAdapter
   - **No**: Continue to next question

4. **Is your dataset for multi-hop question answering?**
   - **Yes**: Use HotpotQAAdapter
   - **No**: Continue to next question

5. **Can your dataset be processed with simple field mapping?**
   - **Yes**: Use StandardJSONAdapter with appropriate configuration
   - **No**: Create a custom adapter

## Configuration vs. Custom DatasetAdapter

In many cases, you can use StandardJSONAdapter with custom configuration instead of creating a new adapter:

```yaml
dataset:
  adapter_class: "prompt_ops.core.datasets.StandardJSONAdapter"
  path: "path/to/dataset.json"
  adapter_params:
    input_field: ["nested", "field", "path"]
    output_field: "answer"
    input_transform: "lambda x: x.strip().lower()"
    default_value: "N/A"
```

Only create a custom dataset adapter when this level of configuration is insufficient for your needs.
