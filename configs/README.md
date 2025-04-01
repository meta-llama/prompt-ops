# prompt-ops configuration

This directory contains YAML configuration files for the prompt-ops tool.

## Configuration Structure

The configuration files follow this structure:

```yaml
model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"
  api_base: "https://openrouter.ai/api/v1"
  temperature: 0.0
  max_tokens: 100000
  cache: false

dataset:
  adapter_class: "prompt_migrator.datasets.joule.adapter.JouleAdapter"  # Full import path to adapter class
  path: "/path/to/dataset.json"
  train_size: 0.25
  validation_size: 0.25
  adapter_params:  # Optional adapter-specific parameters
    param1: value1
    param2: value2

prompt:
  text: |
    Your prompt text here...
  inputs: ["input1", "input2"]
  outputs: ["output1"]

metric:
  # Option 1: Use a built-in metric type
  type: "similarity"  # Built-in signature name
  
  # Option 2: Use a dataset-specific metric class
  # metric_class: "dox"  # Shorthand for prompt_migrator.datasets.dox.metric.DoxMetric
  # params: {}  # Optional parameters for the metric
  
  # Option 3: For custom metrics with the DSPyMetricAdapter:
  # type: "custom"
  # input_mapping:
  #   pred: "prediction"
  #   gold: "reference"
  # output_fields: ["relevance", "accuracy"]
  # score_range: [0, 100]
  # normalize_to: [0, 1]
  # custom_instructions: "Your custom instructions here..."

output:
  directory: "results"
  prefix: "optimized_prompt"

logging:
  level: "INFO"
```

## Available Configuration Files

- `default.yaml`: Default configuration with generic settings
- `joule.yaml`: Configuration for the Joule help documentation benchmark
- `dox.yaml`: Configuration for the DOX delivery documents benchmark

## Dataset Adapters

The prompt-ops tool now supports multiple dataset types through a flexible adapter system:

### Built-in Adapters

- `JouleAdapter`: For the Joule help documentation dataset
- `DoxAdapter`: For the DOX delivery documents dataset

You can specify these adapters in your configuration using either the full import path or a shorthand name:

```yaml
dataset:
  adapter_class: "prompt_migrator.datasets.joule.adapter.JouleAdapter"  # Full import path
  # OR
  adapter_class: "joule"  # Shorthand name (will be resolved to full path)
```

### Custom Adapters

You can create your own dataset adapters by subclassing `DatasetAdapter` and implementing the `adapt` method. Then, specify the full import path to your adapter class in the configuration:

```yaml
dataset:
  adapter_class: "my_package.custom_adapters.MyCustomAdapter"
```

## Metrics

The prompt-ops tool supports multiple metrics for evaluating prompt performance:

### Built-in Metrics

- `similarity`: Uses DSPy's similarity metric for general text comparison
- `dox`: Specialized metric for DOX document extraction tasks

You can specify metrics in your configuration in several ways:

#### Using a built-in metric type:

```yaml
metric:
  type: "similarity"
```

#### Using a dataset-specific metric class:

```yaml
metric:
  metric_class: "dox"  # Shorthand for prompt_migrator.datasets.dox.metric.DoxMetric
  params: {}  # Optional parameters for the metric
```

#### Using a custom metric class with full path:

```yaml
metric:
  metric_class: "my_package.custom_metrics.MyCustomMetric"
  params:
    param1: value1
    param2: value2
```

### Custom Metrics

You can create your own metrics by subclassing `MetricBase` and implementing the `__call__` method. Place your custom metrics in a module structure similar to the built-in metrics, and specify the full import path in your configuration.
  path: "/path/to/custom_dataset.json"
  adapter_params:
    custom_option: "value"
```

The `adapter_params` section allows you to pass custom parameters to your adapter's constructor.

## Using Configuration Files

You can use these configuration files with the test scripts:

```bash
# Use the Joule configuration
python test_with_config.py --config configs/joule.yaml

# Use the DOX configuration
python test_with_config.py --config configs/dox.yaml

# Override specific settings
python test_with_config.py --config configs/joule.yaml --model openrouter/anthropic/claude-3-opus
```

## Command Line Arguments

All configuration settings can be overridden with command line arguments:

```bash
# Model settings
--model MODEL_NAME
--api-base API_BASE
--temperature TEMPERATURE

# Dataset settings
--dataset DATASET_PATH
--adapter-class ADAPTER_CLASS_PATH
--dataset-type {joule,dox}
--train-size TRAIN_SIZE
--val-size VALIDATION_SIZE

# Prompt settings
--prompt "Your prompt text"
--prompt-file /path/to/prompt.txt

# Output settings
--output-dir OUTPUT_DIRECTORY
--output-prefix OUTPUT_PREFIX

# Logging settings
--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}

# Information
--list-adapters  # List available dataset adapters
```

## Examples

See the `examples/joule_optimization_cli.sh` script for usage examples.
