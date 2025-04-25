# llama-prompt-ops Getting Started Guide

Welcome to llama-prompt-ops! This guide will help you understand what's supported out of the box and how to get started quickly.

## 🚀 Quick Start: Choose Your Path

- [🔰 **I'm New to Automated Prompt Engineering**](./basic/readme.md) - Learn the basics with our guided examples
- [🧪 **I Want to Configure Prompt Optimization**](./intermediate/readme.md) - Learn about the intermediate configuration options
- [🚀 **I Have My Own Dataset and Use Case**](./advanced/readme.md) - Adapt prompt-ops to your use case


## 🛠️ Dataset Adapter Selection

| Adapter Type | Dataset Input Format | When to Use |
|--------------|---------------------|-------------|
| StandardJSONAdapter | `[{"question": "What is the capital of France?", "answer": "Paris"}` | For most common datasets with question and answer fields |
| RAGJSONAdapter | `[{"question": "Who wrote Romeo and Juliet?", "context": "Shakespeare wrote many plays...", "answer": "William Shakespeare"}]` | When your dataset includes retrieval contexts |
| Custom Adapter | Any specialized format that doesn't fit the above patterns | When existing adapters don't meet your needs |

See our [detailed adapter selection guide](adapter_selection_guide.md) for more information.

## 📏 Evaluation Metrics


| Metric Type | Use Case | Expected Format | When to Use |
|-------------|----------|-----------------|-------------|
| **ExactMatchMetric** | Simple string matching | Plain text strings | When you need exact string matching between prediction and ground truth |
| **StandardJSONMetric** | Structured JSON evaluation | JSON objects or strings | When evaluating structured JSON responses with specific fields to compare |
| **LLMAsJudgeMetric** | Prompt optimization quality | Text prompts | When evaluating the quality of prompt optimizations across multiple dimensions |
| **Custom Metric** | Specialized evaluation needs | Any custom format | When existing metrics don't meet your evaluation needs |

See our [detailed metric selection guide](./metric_selection_guide.md) for more information.

---

## 🛠️ Multiple Inference Provider Support

llama-prompt-ops supports various inference providers and endpoints to fit your infrastructure needs. See our [detailed guide on inference providers](./inference_providers.md) for configuration examples with:

- OpenRouter (cloud-based API)
- vLLM (local deployment)
- NVIDIA NIMs (optimized containers)
- OpenAI-compatible endpoints


## 📊 Supported Formats at a Glance

### Prompt Formats

- **Text Files**: Plain text files with instructions
- **Inline Text**: Direct text in YAML configuration
- **Template Variables**: Use `{{variable}}` syntax for inputs

### Dataset Formats

- **JSON**: Arrays of objects (most common)
- **CSV**: Tabular data with headers
- **YAML**: Structured data in YAML format

## 🧩 Try Our Examples

We've prepared several complete examples to help you get started:

- [Multi Hop Question Answering](../use-cases/hotpotqa/): Optimize prompts for Multi-hop QA tasks
- [Customer Service](../use-cases/facility-synth/): Categorize and analyze messages

