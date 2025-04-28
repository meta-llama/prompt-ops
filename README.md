<h1 align="center"> Llama Prompt Ops </h1>

<p align="center">
	<a href="https://llama.developer.meta.com/?utm_source=llama-prompt-ops&utm_medium=readme&utm_campaign=main"><img src="https://img.shields.io/badge/Llama_API-Join_Waitlist-brightgreen?logo=meta" /></a>
	<a href="https://llama.developer.meta.com/docs?utm_source=llama-prompt-ops&utm_medium=readme&utm_campaign=main"><img src="https://img.shields.io/badge/Llama_API-Documentation-4BA9FE?logo=meta" /></a>
	
</p>
<p align="center">
	<a href="https://github.com/meta-llama/llama-models/blob/main/models/?utm_source=llama-prompt-ops&utm_medium=readme&utm_campaign=main"><img alt="Llama Model cards" src="https://img.shields.io/badge/Llama_OSS-Model_cards-green?logo=meta" /></a>
	<a href="https://www.llama.com/docs/overview/?utm_source=llama-prompt-ops&utm_medium=readme&utm_campaign=main"><img alt="Llama Documentation" src="https://img.shields.io/badge/Llama_OSS-Documentation-4BA9FE?logo=meta" /></a>
	<a href="https://huggingface.co/meta-llama"><img alt="Hugging Face meta-llama" src="https://img.shields.io/badge/Hugging_Face-meta--llama-yellow?logo=huggingface" /></a>
	
</p>
<p align="center">
	<a href="https://github.com/meta-llama/synthetic-data-kit"><img alt="Llama Tools Syntethic Data Kit" src="https://img.shields.io/badge/Llama_Tools-synthetic--data--kit-orange?logo=meta" /></a>
	<a href="https://github.com/meta-llama/llama-prompt-ops"><img alt="Llama Tools Syntethic Data Kit" src="https://img.shields.io/badge/Llama_Tools-llama--prompt--ops-orange?logo=meta" /></a>
</p>

## What is llama-prompt-ops?

llama-prompt-ops is a Python package that **automatically optimizes prompts** for Llama models. It transforms prompts that might work well with other LLMs into prompts that are optimized for Llama models, improving performance and reliability.

**Key Benefits:**
- **No More Trial and Error**: Stop manually tweaking prompts to get better results
- **Fast Optimization**: Get Llama-optimized prompts minutes with template-based optimization
- **Data-Driven Improvements**: Use your own examples to create prompts that work for your specific use case
- **Measurable Results**: Evaluate prompt performance with customizable metrics

## How It Works

```
┌────────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Original Prompt   │     │  Configuration  │     │     Dataset     │
└────────┬───────────┘     └────────┬────────┘     └────────┬────────┘
         │                          │                       │
         │                          │                       │
         ▼                          ▼                       ▼
         ┌────────────────────────────────────────────────────┐
         │                 prompt-ops migrate                 │
         └────────────────────────────────────────────────────┘
                                  │
                                  │
                                  ▼
                      ┌─────────────────────┐
                      │   Optimized Prompt  │
                      └─────────────────────┘
```

### Simple Workflow

1. **Start with your prompt**: Take your existing prompt that works with other LLMs
2. **Configure optimization**: Set up a simple YAML file with your dataset and preferences
3. **Run optimization**: Execute a single command to transform your prompt
4. **Get results**: Receive a Llama-optimized prompt with performance metrics

### Requirements

To get started with llama-prompt-ops, you'll need:

- Current Prompt: Your existing prompt that you want to optimize for Llama models
- Dataset: A JSON file containing query-answer pairs for evaluation and optimization
- Configuration File: A config file (config.yaml) specifying tool behavior, parameters, and optimization details (see [example configuration](configs/facility-simple.yaml))


## Quick Start (5 minutes)

### Installation

```bash
# Create a virtual environment
conda create -n prompt-ops python=3.10
conda activate prompt-ops

# Install from PyPI
pip install llama-prompt-ops

# OR install from source
git clone https://github.com/meta-llama/llama-prompt-ops.git
cd llama-prompt-ops
pip install -e .
```



### Set Up Your API Key

Create a `.env` file in your project directory with your API key:

```bash
echo "OPENROUTER_API_KEY=your_key_here" > .env
```

### Create a Simple Configuration

Create a file named `config.yaml` with this basic configuration:

```yaml
prompt:
  text: |
    You are a helpful assistant. Extract and return a json with the following keys and values:
    - "urgency" as one of `high`, `medium`, `low`
    - "sentiment" as one of `negative`, `neutral`, `positive`
    - "categories" Create a dictionary with categories as keys and boolean values (True/False)
    Your complete message should be a valid json string that can be read directly.
  inputs: ["question"]
  outputs: ["answer"]

model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"

optimization:
  strategy: "llama"
  fast: true
```

### Run Optimization

```bash
prompt-ops migrate --config config.yaml
```

The optimized prompt will be saved to the `results` directory with performance metrics comparing the original and optimized versions.

### Try the Built-in Example

For a more complete example with a dataset, run:

```bash
prompt-ops migrate --config configs/facility-simple.yaml
```

This example demonstrates how prompt-ops migrates a customer service analysis prompt to Llama models, categorizing messages by urgency, sentiment, and topic categories.

### Prompt Transformation Example

Below is an example of how prompt-ops transforms a prompt from OpenAI to Llama:

| Original OpenAI Prompt                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Optimized Llama Prompt                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| You are a helpful assistant. Extract and return a json with the following keys and values:<br>- "urgency" as one of `high`, `medium`, `low`<br>- "sentiment" as one of `negative`, `neutral`, `positive`<br>- "categories" Create a dictionary with categories as keys and boolean values (True/False), where the value indicates whether the category is one of the best matching support category tags from: `emergency_repair_services`, `routine_maintenance_requests`, etc.<br><br>Your complete message should be a valid json string that can be read directly. | You are an expert in analyzing customer service messages. Your task is to categorize the following message based on urgency, sentiment, and relevant categories.<br><br>Analyze the message and return a JSON object with these fields:<br>1. "urgency": Classify as "high", "medium", or "low" based on how quickly this needs attention<br>2. "sentiment": Classify as "negative", "neutral", or "positive" based on the customer's tone<br>3. "categories": Create a dictionary with facility management categories as keys and boolean values<br><br>Only include these exact keys in your response. Return a valid JSON object without code blocks, prefixes, or explanations. |

## Key Features

- **YAML Configuration**: Define your entire optimization pipeline in a single YAML file
- **Standardized Dataset Adapters**: Easily work with different dataset formats (JSON, CSV, YAML)
- **Customizable Metrics**: Evaluate prompt performance with configurable metrics
- **Multiple Inference Providers**: Support for OpenRouter, vLLM, NVIDIA NIMs, and OpenAI-compatible endpoints
- **Fast Optimization Mode**: Get optimized prompts in seconds without a dataset
- **Comprehensive Evaluation**: Compare original and optimized prompts with detailed metrics

## Documentation and Examples

For more detailed information, check out these resources:

- [Quick Start Guide](docs/basic/readme.md): Get up and running with prompt-ops in 5 minutes
- [Intermediate Configuration Guide](docs/intermediate/readme.md): Learn how to configure datasets, metrics, and optimization strategies
- [Adapter Selection Guide](docs/adapter_selection_guide.md): Choose the right adapter for your dataset format
- [Metric Selection Guide](docs/metric_selection_guide.md): Select appropriate evaluation metrics for your use case
- [Inference Providers Guide](docs/inference_providers.md): Configure different model providers and endpoints

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
