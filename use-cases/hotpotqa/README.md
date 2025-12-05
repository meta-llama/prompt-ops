# HotpotQA Use Case

This directory contains the necessary files to run prompt optimization for multi-hop question answering using the HotpotQA dataset.

## Getting Started

### 1. Download the Dataset

Before you can run the optimization, you need to download the HotpotQA dataset. Run the following command from this directory:

```bash
curl -O http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json
```

This will download the development set with distractors.

### 2. Configure Your Environment

Make sure you have set up your API keys in the `.env` file at the root of the project:

```
OPENROUTER_API_KEY=your_key_here
# or other provider-specific keys
GROQ_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here
```

LiteLLM will automatically detect the correct API key based on your model name prefix (e.g., `openrouter/`, `groq/`).

### 3. Run Optimization

From the root directory of the project, run:

```bash
prompt-ops migrate --config configs/hotpotqa.yaml
```

## Dataset Information

The HotpotQA dataset is a question answering dataset featuring complex, multi-hop questions that require reasoning across multiple documents to answer. Each example contains:

- A question requiring multi-hop reasoning
- Supporting facts from multiple documents
- Distractor documents that are not relevant to the question
- The correct answer
