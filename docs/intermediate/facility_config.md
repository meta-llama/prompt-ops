# Intermediate Guide: Facility YAML Configuration

> **Note:** If you're new to prompt-ops, start with the [Quick Start Guide](../basic/quick_start.md) before exploring these advanced options.

## Overview

This intermediate guide explores the configuration options available for optimizing prompts in the facility management classification task. We'll examine each component of the YAML configuration file in detail, explaining what each setting does and how to customize it for your specific needs.

The facility management classification task involves categorizing customer service messages by:
1. Urgency level
2. Customer sentiment
3. Relevant service categories

By understanding the advanced configuration options, you can fine-tune the optimization process to achieve better results for your specific use case.

## Complete Configuration Structure

Here's the complete configuration structure for the facility management classification task:

```yaml
# Model Configuration
model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"
  api_base: "https://openrouter.ai/api/v1"
  temperature: 0.0
  max_tokens: 2048
  top_p: 0.95
  cache: false

# Dataset Configuration
dataset:
  adapter_class: "prompt_ops.core.datasets.ConfigurableJSONAdapter"
  path: "../dataset/facility-synth/facility_v2_test.json"
  train_size: 0.7
  validation_size: 0.15
  # These parameters can be placed directly at the dataset level
  input_field: ["fields", "input"]
  golden_output_field: "answer"
  # Optional parameters
  seed: 42
  shuffle: true

# Prompt Configuration
prompt:
  file: "../dataset/facility-synth/facility_prompt_sys.txt"  # Reference to prompt file instead of inline text
  inputs: ["question"]
  outputs: ["answer"]

# Metric Configuration
metric:
  class: "standard_json"  # Can use shorthand instead of full class path
  evaluation_mode: "flattened"
  fields: ["urgency", "sentiment", "categories"]
  nested_fields:
    categories: [
      "emergency_repair_services", 
      "routine_maintenance_requests", 
      "quality_and_safety_concerns", 
      "specialized_cleaning_services", 
      "general_inquiries", 
      "sustainability_and_environmental_practices", 
      "training_and_support_requests", 
      "cleaning_services_scheduling", 
      "customer_feedback_and_complaints", 
      "facility_management_issues"
    ]
  required_fields: ["urgency", "sentiment", "categories"]
  weights:  # Renamed from field_weights to weights
    urgency: 1.0
    sentiment: 1.0
    categories: 1.0
  strict_json: false

# Optimization Settings
optimization:
  strategy: "basic"
  max_rounds: 3
  max_examples_per_round: 5
  max_prompt_length: 2048
  num_candidates: 5
  bootstrap_examples: 4
  num_threads: 36
  max_errors: 5
  disable_progress_bar: false
  save_intermediate: false
  model_family: "llama"
```

Now let's explore each section in detail.

## Model Configuration

The `model` section defines which language model to use for both prompt optimization and inference. This is the LLM that will process your dataset examples, generate responses, and be used to evaluate and refine your prompts:

```yaml
model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"
  api_base: "https://openrouter.ai/api/v1"
  temperature: 0.0
  max_tokens: 2048
  top_p: 0.95
  cache: false
```

| Parameter | Description | Recommended Values |
|-----------|-------------|-------------------|
| `name` | The model identifier in LiteLLM format (`provider/model_name`) | For Llama models: `openrouter/meta-llama/llama-3.3-70b-instruct` |
| `api_base` | The API endpoint for the provider | OpenRouter: `https://openrouter.ai/api/v1`<br>Together: `https://api.together.com/v1` |
| `temperature` | Controls randomness (0.0-1.0) | For classification: `0.0` (deterministic)<br>For creative tasks: `0.7` |
| `max_tokens` | Maximum response length | For JSON outputs: `2048` |
| `top_p` | Nucleus sampling parameter (0.0-1.0) | `0.95` for balanced results |
| `cache` | Whether to cache model responses | `true` to save API calls during development |

**Advanced Options:**
- `top_k`: Limits token selection to the top K most likely tokens
- `frequency_penalty`: Reduces repetition by penalizing tokens that have already appeared
- `presence_penalty`: Encourages diversity by penalizing tokens based on their presence

## Dataset Configuration

The `dataset` section defines how to load and process your examples:

```yaml
dataset:
  adapter_class: "prompt_ops.core.datasets.ConfigurableJSONAdapter"
  path: "/path/to/dataset/facility-synth/facility_v2_test.json"
  train_size: 0.7
  validation_size: 0.15
  seed: 42
  shuffle: true
  input_field: ["fields", "input"]
  golden_output_field: "answer"
```

| Parameter | Description | Recommended Values |
|-----------|-------------|-------------------|
| `adapter_class` | The class that handles dataset loading | Standard JSON: `prompt_ops.core.datasets.ConfigurableJSONAdapter`<br>For RAG: `prompt_ops.core.datasets.RAGJSONAdapter` |
| `path` | Path to your dataset file | Absolute path recommended |
| `train_size` | Proportion of data used for training | `0.7` (70%) |
| `validation_size` | Proportion of data used for validation | `0.15` (15%) |
| `seed` | Random seed for reproducibility | Any integer (e.g., `42`) |
| `shuffle` | Whether to shuffle the dataset | `true` for better generalization |
| `input_field` | Where to find the input in each example | For nested fields: `["fields", "input"]`<br>For top-level: `"input"` |
| `golden_output_field` | Where to find the expected output | For JSON responses: `"answer"` |

**Advanced Adapter Options:**
- For complex datasets, you can create a custom adapter by extending `DatasetAdapter`
- The `StandardJSONAdapter` supports flexible field mapping and transformations

## Prompt Configuration

The `prompt` section defines the starting prompt and how it interacts with the dataset. You can provide the prompt in two ways:

```yaml
prompt:
# Option 1: Inline Text
  text: |
    Giving the following message:
    ---
    {{question}}
    ---
    Extract and return a json with the following keys and values:
    - "urgency" as one of `high`, `medium`, `low`
    - "sentiment" as one of `negative`, `neutral`, `positive`
    - "categories" Create a dictionary with categories as keys and boolean values... 
# Option 2: File Path
  file: "../dataset/facility-synth/facility_prompt_sys.txt" 
  inputs: ["question"]
  outputs: ["answer"]
```

| Parameter | Description | Recommended Values |
|-----------|-------------|-------------------|
| `text` | The prompt template text | Include clear instructions and output format |
| `file` | Alternative: path to a prompt file | Use instead of `text` for longer prompts |
| `inputs` | Fields from dataset to insert into prompt | Match the placeholders in your prompt (e.g., `["question"]`) |
| `outputs` | Fields to capture from model response | For JSON outputs: `["answer"]` |

**Prompt Template Tips:**
- Use placeholders like `{{question}}` that will be replaced with dataset values
- For Llama models, be explicit about output format requirements
- Include examples of the expected output format for better results
- You can use either `text` or `file`, but not both

## Metric Configuration

The `metric` section defines how to evaluate prompt performance:

```yaml
metric:
  class: "prompt_ops.core.metrics.StandardJSONMetric"
  params:
  evaluation_mode: "flattened"
  fields: ["urgency", "sentiment", "categories"]
  nested_fields:
    categories: [
      "emergency_repair_services", 
      "routine_maintenance_requests",
      # ... other categories
    ]
  required_fields: ["urgency", "sentiment", "categories"]
  weights:  # Renamed from field_weights to weights
    urgency: 1.0
    sentiment: 1.0
    categories: 1.0
  strict_json: false
```

| Parameter | Description | Recommended Values |
|-----------|-------------|-------------------|
| `class` | The metric class to use | For JSON: `standard_json` or `prompt_ops.core.metrics.StandardJSONMetric`<br>For similarity: `similarity` |
| `evaluation_mode` | How to compare outputs | For nested JSON: `"flattened"`<br>For specific field validation: `"field_based"` |
| `fields` | Which fields to evaluate | List all important fields: `["urgency", "sentiment", "categories"]` |
| `nested_fields` | Subfields within nested structures | For categories: list all possible category values |
| `required_fields` | Fields that must be present | Critical fields: `["urgency", "sentiment", "categories"]` |
| `weights` | Importance of each field | Set weights for fields (e.g., `categories: 1.0`) |
| `strict_json` | Whether to require exact JSON | `false` allows extracting JSON from text |

**Evaluation Modes Explained:**
- `flattened`: Converts nested JSON to key-value pairs before comparison (best for complex structures)
- `field_based`: Evaluates each field individually with explicit validation (best for critical fields)

## Optimization Settings

The `optimization` section controls how prompt-ops approaches the optimization process:

```yaml
optimization:
  strategy: "basic"
  max_rounds: 3
  max_examples_per_round: 5
  max_prompt_length: 2048
  num_candidates: 5
  bootstrap_examples: 4
  num_threads: 36
  max_errors: 5
  disable_progress_bar: false
  save_intermediate: false
  model_family: "llama"
```

| Parameter | Description | Recommended Values |
|-----------|-------------|-------------------|
| `strategy` | Optimization approach | For quick results: `"basic"`<br>For thorough optimization: `"intermediate"` |
| `max_rounds` | Number of optimization iterations | `3` for basic strategy<br>`5` for intermediate strategy |
| `max_examples_per_round` | Examples to use per round | `5` for faster results<br>`10` for better quality |
| `max_prompt_length` | Maximum length of optimized prompt | `2048` for most tasks<br>`4096` for complex tasks |
| `num_candidates` | Prompt variations to try | `5` for balanced exploration |
| `bootstrap_examples` | Examples to include in prompt | `4` for few-shot learning |
| `num_threads` | Parallel processing threads | `36` for faster processing on powerful machines |
| `max_errors` | Errors before stopping | `5` to avoid wasting API calls |
| `disable_progress_bar` | Hide progress display | `false` to see progress |
| `save_intermediate` | Save interim results | `true` for debugging |
| `model_family` | Model-specific optimizations | `"llama"` for Llama models |

**Strategy Options Explained:**
- `basic`: Makes minimal changes to preserve the original prompt structure (fastest)
- `intermediate`: Balanced approach with moderate changes (recommended)
- `advanced`: More extensive modifications for maximum performance (slowest)

## Running with Advanced Configuration

To run prompt-ops with your advanced configuration:

```bash
# Set your API key
export OPENROUTER_API_KEY=your_key_here

# Run optimization
prompt-ops migrate --config configs/facility.yaml
```

You can override specific configuration values via command line:

```bash
# Override model with a different Llama endpoint
prompt-ops migrate --config configs/facility.yaml --model together/meta-llama/Llama-3-70b-chat

# Override dataset path
prompt-ops migrate --config configs/facility.yaml --dataset-path /path/to/new/dataset.json
```

## Advanced Output Analysis

After optimization, prompt-ops generates detailed output files:

1. **JSON Results File**: Contains performance metrics and the optimized prompt
   - Located in: `results/facility_TIMESTAMP.json`

2. **YAML Configuration**: Ready-to-use optimized configuration
   - Located in: `results/facility_TIMESTAMP.yaml`

The optimized prompt typically includes:
- An improved system prompt
- Few-shot examples selected from your dataset
- Formatting improvements for better model compatibility

## Customizing for Different Tasks

While this tutorial focuses on facility classification, you can adapt the configuration for other tasks:

- **Text Summarization**: Change output fields and evaluation metrics
- **Question Answering**: Use RAGJSONAdapter for context-based QA
- **Code Generation**: Modify evaluation to focus on functional correctness

## Conclusion

This intermediate guide has covered the main configuration options available in prompt-ops for optimizing prompts in the facility management classification task. By understanding and customizing these settings, you can achieve better results for your specific use case.

For more advanced use cases, such as creating custom adapters and metrics for specialized datasets or evaluation requirements, see the [Advanced Guide: Creating Custom Adapters and Metrics](../advanced/custom_adapters_metrics.md).

