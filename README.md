<h1 align="center"> Llama Prompt Ops </h1>

## What is llama-prompt-ops?

llama-prompt-ops is a Python package that **automatically optimizes prompts** for Llama models. It transforms prompts that work well with other LLMs into prompts that are optimized for Llama models, improving performance and reliability.

**Key Benefits:**
- **No More Trial and Error**: Stop manually tweaking prompts to get better results
- **Fast Optimization**: Get Llama-optimized prompts minutes with template-based optimization
- **Data-Driven Improvements**: Use your own examples to create prompts that work for your specific use case
- **Measurable Results**: Evaluate prompt performance with customizable metrics

## Requirements

To get started with llama-prompt-ops, you'll need:

- Existing System Prompt: Your existing system prompt that you want to optimize
- Existing Query-Response Dataset: A JSON file containing query-response pairs (as few as 50 examples) for evaluation and optimization (see [prepare your dataset](#preparing-your-data) below)
- Configuration File: A YAML configuration file (config.yaml) specifying model hyperparameters, and optimization details (see [example configuration](configs/facility-simple.yaml))

## How It Works

```
┌──────────────────────────┐    ┌────────────────────────────────┐     ┌───────────────────────┐    
│  Existing System Prompt  │    │     set(query, responses)      │     │  YAML Configuration   │    
└────────────┬─────────────┘    └────────────────┬───────────────┘     └────────────┬──────────┘    
             │                                   │                                  │               
             │                                   │                                  │               
             ▼                                   ▼                                  ▼               
         ┌────────────────────────────────────────────────────────────────────────────┐
         │                         llama-prompt-ops migrate                           │
         └────────────────────────────────────────────────────────────────────────────┘
                                                 │
                                                 │
                                                 ▼
                                     ┌──────────────────────┐
                                     │   Optimized Prompt   │
                                     └──────────────────────┘
```

### Simple Workflow

1. **Start with your system prompt**: Take your existing system prompt that works with other LLMs
2. [**Prepare your dataset**](#preparing-your-data): Create a JSON file with query-response pairs for evaluation and optimization
3. [**Configure optimization**](#create-a-simple-configuration): Set up a simple YAML file with your dataset and preferences
4. [**Run optimization**](#run-optimization): Execute a single command to transform your prompt
5. [**Get results**](#prompt-transformation-example): Receive a Llama-optimized prompt with performance metrics



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

You can get an OpenRouter API key by creating an account at [OpenRouter](https://openrouter.ai/).

### Create a Simple Configuration

Create a file named `config.yaml` with this basic configuration:

```yaml
system_prompt:
  file: "../use-cases/facility-synth/facility_prompt_sys.txt"

# Dataset configuration
dataset:
  path: "../use-cases/facility-synth/facility_v2_test.json"
  input_field: ["fields", "input"]
  golden_output_field: "answer"

# Model configuration (minimal required settings)
model:
  task_model: "openrouter/meta-llama/llama-3.3-70b-instruct"
  proposer_model: "openrouter/meta-llama/llama-3.3-70b-instruct"

# Metric configuration (simplified but maintains compatibility)
metric:
  class: "prompt_ops.core.metrics.FacilityMetric"
  strict_json: false
  output_field: "answer"

# Optimization settings
optimization:
  strategy: "llama"  # (llama, basic, advanced)

```

### Run Optimization

```bash
llama-prompt-ops migrate --config config.yaml
```

The optimized prompt will be saved to the `results` directory with performance metrics comparing the original and optimized versions.


### Prompt Transformation Example

Below is an example of a transformed system prompt from proprietary LM to Llama:

| Original Proprietary LM Prompt | Optimized Llama Prompt |
| --- | --- |
| You are a helpful assistant. Extract and return a JSON with the following keys and values:<br><br>1. "urgency": one of `high`, `medium`, `low`<br>2. "sentiment": one of `negative`, `neutral`, `positive`<br>3. "categories": Create a dictionary with categories as keys and boolean values (True/False), where the value indicates whether the category matches tags like `emergency_repair_services`, `routine_maintenance_requests`, etc.<br><br>Your complete message should be a valid JSON string that can be read directly. | You are an expert in analyzing customer service messages. Your task is to categorize the following message based on urgency, sentiment, and relevant categories.<br><br>Analyze the message and return a JSON object with these fields:<br><br>1. "urgency": Classify as "high", "medium", or "low" based on how quickly this needs attention<br>2. "sentiment": Classify as "negative", "neutral", or "positive" based on the customer's tone<br>3. "categories": Create a dictionary with facility management categories as keys and boolean values<br><br>Only include these exact keys in your response. Return a valid JSON object without code blocks, prefixes, or explanations. |


### Preparing Your Data

To use llama-prompt-ops for prompt optimization, you'll need to prepare a dataset with your prompts and expected responses. The standard format is a JSON file structured like this:

```json
[
    {
        "question": "Your input query here",
        "answer": "Expected response here"
    },
    {
        "question": "Another input query",
        "answer": "Another expected response"
    }
]
```

If your data matches this format, you can use the built-in [`StandardJSONAdapter`](src/prompt_ops/core/datasets.py) which will handle it automatically.

### Custom Data Formats

If your data is formatted differently, and there isn't a built-in dataset adapter, you can create a custom dataset adapter by extending the `DatasetAdapter` class. See the [Dataset Adapter Selection Guide](docs/dataset_adapter_selection_guide.md) for more details.

## Multiple Inference Provider Support

llama-prompt-ops supports various inference providers and endpoints to fit your infrastructure needs. See our [detailed guide on inference providers](./docs/inference_providers.md) for configuration examples with:

- OpenRouter (cloud-based API)
- vLLM (local deployment)
- NVIDIA NIMs (optimized containers)

## Documentation and Examples

For more detailed information, check out these resources:

- [Quick Start Guide](docs/basic/readme.md): Get up and running with llama-prompt-ops in 5 minutes
- [Intermediate Configuration Guide](docs/intermediate/readme.md): Learn how to configure datasets, metrics, and optimization strategies
- [Dataset Adapter Selection Guide](docs/dataset_adapter_selection_guide.md): Choose the right adapter for your dataset format
- [Metric Selection Guide](docs/metric_selection_guide.md): Select appropriate evaluation metrics for your use case
- [Inference Providers Guide](docs/inference_providers.md): Configure different model providers and endpoints

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
