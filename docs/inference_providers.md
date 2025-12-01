# Using Different Inference Providers with prompt-ops

This guide demonstrates how to configure prompt-ops to work with various inference providers, including OpenRouter, vLLM, and NVIDIA NIMs. By changing the model configuration in your YAML files, you can easily switch between different backends without modifying your code.

## Understanding Model Configuration

In prompt-ops, model configuration is specified in the `model` section of your YAML configuration file. The basic configuration looks like this:

```yaml
model:
  name: "openrouter/meta-llama/llama-3.1-8b-instruct"
  temperature: 0.0
  max_tokens: 40960
```

**prompt-ops uses [LiteLLM](https://docs.litellm.ai/docs/) as the unified API client** to handle all LLM API calls. LiteLLM provides automatic provider detection based on the model name prefix (e.g., `openrouter/`, `groq/`, `together_ai/`) and looks for the corresponding environment variable (e.g., `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `TOGETHERAI_API_KEY`).

## Available Inference Providers

### 1. OpenRouter

[OpenRouter](https://openrouter.ai/) provides access to a wide range of models from different providers through a unified API.

```yaml
model:
  name: "openrouter/meta-llama/llama-3.1-8b-instruct"
  temperature: 0.0
  max_tokens: 40960
```

Set your API key as an environment variable (LiteLLM will auto-detect it):

```bash
export OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 2. vLLM

[vLLM](https://github.com/vllm-project/vllm) is an open-source library for fast LLM inference. It's particularly useful for running models locally or on your own infrastructure.

```yaml
model:
  name: "hosted_vllm/meta-llama/Llama-3.1-8B-Instruct"
  api_base: "http://localhost:8000/v1"
  temperature: 0.0
  max_tokens: 4096
```

To run vLLM locally, you would first start the vLLM server:

```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-8B-Instruct --tensor-parallel-size=1
```

3.

### 4. NVIDIA NIMs

[NVIDIA NIMs](https://docs.nvidia.com/nim/large-language-models/latest/introduction.html) (NVIDIA Inference Microservices) provide optimized containers for running LLMs on NVIDIA GPUs.

```yaml
model:
  name: "openai/meta/llama-3.1-8b-instruct"  # Format: openai/{model_name}
  api_base: "http://localhost:8000/v1"
  api_key: "any_string_for_localhost"  # Can be any string for local deployments
  temperature: 0.0
  max_tokens: 4096
```

To run a NIM container locally:

```bash
docker run -it --rm --name=nim \
  --runtime=nvidia \
  --gpus 1 \
  --shm-size=16GB \
  -e NGC_API_KEY=<YOUR NGC API KEY> \
  -v "~/.cache/nim:/opt/nim/.cache" \
  -u $(id -u) \
  -p 8000:8000 \
  nvcr.io/nim/meta/llama-3.1-8b-instruct:1.5.0
```

### 4. Together AI

[Together AI](https://www.together.ai/) provides a platform for running various open-source models with optimized performance and competitive pricing.

```yaml
model:
  name: "together_ai/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
  temperature: 0.0
  max_tokens: 4096
```

To use Together AI, you'll need to:

1. Sign up for an account at [Together AI](https://www.together.ai/)
2. Generate an API key from your account dashboard
3. Set the API key as an environment variable (LiteLLM will auto-detect it):

```bash
export TOGETHERAI_API_KEY=your_api_key_here
```

Then run the optimization:

```bash
prompt-ops migrate
```

### 5. Groq


```yaml
model:
  task_model: groq/meta-llama/llama-4-maverick-17b-128e-instruct
  proposer_model: groq/meta-llama/llama-4-maverick-17b-128e-instruct
  api_base: https://api.groq.com/openai/v1
```

```bash
export GROQ_API_KEY=your_api_key_here
```

Then run the optimization:

```bash
prompt-ops migrate
```

## Advanced Configuration

### Using Different Models for Task and Proposer

prompt-ops allows you to specify different models for the task execution and the prompt proposal process:

```yaml
model:
  task_model: "openrouter/meta-llama/llama-3.1-8b-instruct"
  proposer_model: "openrouter/meta-llama/llama-3.3-70b-instruct"
  api_base: "https://openrouter.ai/api/v1"
  temperature: 0.0
  max_tokens: 4096
```

## Running prompt-ops with Different Providers

To run prompt-ops with your configuration:

```bash
# Set your provider-specific API key
export OPENROUTER_API_KEY=your_key  # For OpenRouter models (openrouter/...)
export GROQ_API_KEY=your_key        # For Groq models (groq/...)
export TOGETHERAI_API_KEY=your_key  # For Together AI models (together_ai/...)

# Run with any configuration
prompt-ops migrate --config configs/your_config.yaml
```

**How LiteLLM Works:** LiteLLM automatically detects the provider from your model name prefix (e.g., `openrouter/model`, `groq/model`, `together_ai/model`) and looks for the corresponding environment variable (`OPENROUTER_API_KEY`, `GROQ_API_KEY`, `TOGETHERAI_API_KEY`). No manual API routing required!

For more information on supported providers, environment variables, and configuration options, refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/set_keys).
