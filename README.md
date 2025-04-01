# prompt-ops

> Automated prompt engineering and optimization for LLMs like Llama

## What is prompt-ops?

prompt-ops is a Python package that automates the process of optimizing prompts for large language models, with a focus on Llama models. It provides both fast template-based optimization and thorough dataset-driven approaches to help you get the best performance from your LLM prompts without manual trial and error.

## Why use prompt-ops?

- **Automated Optimization**: Eliminates manual prompt engineering through data-driven optimization techniques
- **Improved Output Quality**: Enhances LLM responses by applying model-specific best practices and formatting
- **Simple Migration**: Easily migrate prompts from other LLM models to Llama with configurable strategies
- **Flexible Approaches**: Choose between fast template-based optimization or thorough dataset-based optimization
- **Standardized Evaluation**: Evaluate prompt performance with customizable metrics and datasets

## Quick Start (5 minutes)

### Installation

```bash
# From PyPI
pip install prompt-ops

# From source
git clone https://github.com/yourusername/prompt-ops.git
cd prompt-ops
pip install -e .
```

### Basic Usage

1. Create a `.env` file in the project root:

```bash
# Create and open .env file
echo "OPENROUTER_API_KEY=your_key_here" > .env
```

2. Run the facility-simple example to analyze customer service messages:

```bash
# Install the package
pip install -e .

# Run with the simple facility configuration
prompt-ops migrate --config configs/facility-simple.yaml
```

This example demonstrates how prompt-ops migrates a customer service analysis prompt from OpenAI to Llama models. The prompt analyzes customer messages, categorizing them by urgency (high/medium/low), sentiment (positive/neutral/negative), and topic categories. The optimized prompt will be saved to the `results` directory with performance metrics comparing the original and optimized versions.

### Prompt Transformation Example

Below is an example of how prompt-ops transforms a prompt from OpenAI to Llama:

| Original OpenAI Prompt | Optimized Llama Prompt |
|------------------------|------------------------|
| You are a helpful assistant. Extract and return a json with the follwoing keys and values:<br>- "urgency" as one of `high`, `medium`, `low`<br>- "sentiment" as one of `negative`, `neutral`, `positive`<br>- "categories" Create a dictionary with categories as keys and boolean values (True/False), where the value indicates whether the category is one of the best matching support category tags from: `emergency_repair_services`, `routine_maintenance_requests`, etc.<br><br>Your complete message should be a valid json string that can be read directly. | You are an expert in analyzing customer service messages. Your task is to categorize the following message based on urgency, sentiment, and relevant categories.<br><br>Analyze the message and return a JSON object with these fields:<br>1. "urgency": Classify as "high", "medium", or "low" based on how quickly this needs attention<br>2. "sentiment": Classify as "negative", "neutral", or "positive" based on the customer's tone<br>3. "categories": Create a dictionary with facility management categories as keys and boolean values<br><br>Only include these exact keys in your response. Return a valid JSON object without code blocks, prefixes, or explanations. |


## Key Features

- **Multiple Optimization Strategies**: Choose from template-based or dataset-driven approaches
- **Standardized Dataset Adapters**: Easily work with different dataset formats using built-in or custom adapters
- **Customizable Metrics**: Evaluate prompt performance with configurable metrics
- **YAML Configuration**: Define your entire optimization pipeline in a single YAML file
- **CLI Interface**: Run optimizations directly from the command line
- **Llama-Specific Optimizations**: Apply best practices for Llama models automatically

## Documentation and Examples

For more detailed information, check out these resources:

- [Quick Start Guide](docs/basic/quick_start.md): Get up and running with prompt-ops
- [Intermediate Configuration Example](docs/intermediate/facility_config.md): Learn how to configure prompt-ops for customer service tasks
- [Advanced Customization](docs/advanced/custom_adapters_metrics.md): Create your own dataset adapters and evaluation metrics

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
