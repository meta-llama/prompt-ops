# Prompt Ops

A Python package for migrating and optimizing prompts from other LLMs to Llama using configurable strategies.

## Overview

The Prompt Ops package provides developers with functionality to migrate and optimize prompts from other LLMs to Llama using configurable strategies. This package offers a flexible, pluggable API for prompt optimization with multiple integration points.

## Installation

### From Source

```bash
git clone <repository-url>
cd prompt-ops
pip install -e .
```

### Development Installation

For development, install with additional dependencies:

```bash
pip install -e ".[dev]"
```

### Environment Setup with uv

#### Installing uv

```bash
# Install uv using pip
pip install uv

# Or on macOS with Homebrew
brew install uv
```

#### Creating a Virtual Environment for Prompt Ops

```bash
# Create a dedicated virtual environment for prompt-ops
uv venv prompt-ops-env

# Activate the environment
source prompt-ops-env/bin/activate  # On Unix/macOS
# or
prompt-ops-env\Scripts\activate     # On Windows

# Navigate to the prompt-ops directory
cd /path/to/prompt-ops
```

#### Installing Prompt Ops Dependencies with uv

```bash
# Install prompt-ops and its core dependencies
uv pip install -e .

# For development work (includes testing and code quality tools)
uv pip install -e ".[dev]"

# This will install all dependencies including:
# - dspy for prompt optimization
# - numpy and scipy for numerical operations
# - pandas for data manipulation
# - openai and litellm for model access
```

#### Using uv with Existing Conda Environment for Prompt Ops

```bash
# If you prefer using conda for environment management
# First create a conda environment with Python 3.10
conda create -n prompt-ops python=3.10 -y

# Activate the conda environment
conda activate prompt-ops

# Install prompt-ops dependencies with uv (much faster than regular pip)
uv pip install -e ".[dev]"
```

Using uv can make dependency resolution and installation much faster, especially for large projects with complex dependency trees.

## Usage

### Basic Python Usage

```python
from prompt_ops.core.migrator import PromptMigrator
from prompt_ops.core.prompt_strategies import LightOptimizationStrategy

# Create a migrator with a specific strategy
migrator = PromptMigrator(strategy=LightOptimizationStrategy())

# Optimize a prompt
optimized_prompt = migrator.optimize(
    {"text": "Your original prompt here", "inputs": ["question"], "outputs": ["answer"]}
)
print(optimized_prompt.signature.instructions)
```

### Using Dataset Adapters

The package includes a standardized dataset loading system using the Dataset Adapters pattern:

```python
from prompt_ops.core.migrator import PromptMigrator
from prompt_ops.core.prompt_strategies import LightOptimizationStrategy
from prompt_ops.datasets.custom import CustomAdapter  # Import a specific adapter

# Create a strategy and migrator
strategy = LightOptimizationStrategy(
    model_name="llama-70b",
    metric=your_metric,
    task_model=model,
    prompt_model=model
)

migrator = PromptMigrator(
    strategy=strategy,
    task_model=model,
    prompt_model=model
)

# Create an adapter for your dataset
adapter = CustomAdapter(dataset_path="/path/to/your/dataset.json")

# Load dataset using adapter
trainset, valset, testset = migrator.load_dataset_with_adapter(
    adapter, train_size=0.25, validation_size=0.25
)

# Optimize a prompt with the loaded dataset
optimized = migrator.optimize(
    {
        "text": "Your original prompt here", 
        "inputs": ["question", "context"], 
        "outputs": ["answer"]
    },
    trainset=trainset,
    valset=valset,
    testset=testset,
    save_to_file=True,
    file_path="optimized_prompt.txt"
)
```

## Features

- Multiple optimization strategies (Light, Heavy)
- Customizable metrics for evaluation
- Standardized dataset loading with Dataset Adapters
- Integration with Llama models

## Dataset Adapters

The package includes a standardized way to load and process different datasets using the Dataset Adapters pattern:

### Available Adapters

The package includes several dataset adapters. You can also create your own custom adapters.

### Creating a Custom Adapter

To create an adapter for a new dataset, subclass `DatasetAdapter` and implement the `adapt` method:

```python
from prompt_migrator.core.datasets import DatasetAdapter

class MyCustomAdapter(DatasetAdapter):
    def adapt(self):
        data = self.load_raw_data()
        return [
            {
                "inputs": {
                    "field1": doc["your_input_field1"],
                    "field2": doc["your_input_field2"],
                },
                "outputs": {
                    "field1": doc["your_output_field"],
                },
                "metadata": {  # Optional
                    "extra_info": doc["some_extra_info"],
                }
            }
            for doc in data
        ]
```

## Examples

The repository includes example implementations for different use cases. Check the `examples/` directory for more information.

## License

Proprietary - Internal Meta use only
