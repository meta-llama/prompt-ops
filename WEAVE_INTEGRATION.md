# W&B Weave Integration Guide

This guide explains how to use the W&B Weave integration with llama-prompt-ops for comprehensive tracking of prompt optimization experiments.

## Overview

The Weave integration provides three core capabilities:

1. **Prompt Versioning**: Automatically tracks original and optimized prompts using `weave.StringPrompt`
2. **Dataset Versioning**: Tracks training/validation datasets using `weave.Dataset`  
3. **LLM Call Tracing**: Automatically traces all LLM calls during optimization via `weave.init()`

## Requirements

- Install Weave: `pip install weave>=0.51.0` (already included in llama-prompt-ops dependencies)
- W&B account (sign up at https://wandb.ai)

## Quick Start

### 1. Enable Weave in Configuration

Add a `weave` section to your YAML configuration file:

```yaml
# Your existing configuration...
model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"
  # ... other model config

dataset:
  path: "path/to/dataset.json"
  # ... other dataset config

# Add Weave tracking configuration
weave:
  enabled: true
  project_name: "llama-prompt-optimization"
  entity: "your-wandb-entity"  # Optional: your W&B team/entity
```

### 2. Run Optimization with Weave Tracking

```bash
# Using config file (Weave enabled/disabled based on config)
llama-prompt-ops migrate --config your-config.yaml

# Force enable Weave (overrides config setting)
llama-prompt-ops migrate --config your-config.yaml --weave

# Force disable Weave (overrides config setting)
llama-prompt-ops migrate --config your-config.yaml --no-weave
```

### 3. View Results in Weave UI

After running optimization:
1. Go to https://wandb.ai/your-entity/your-project-name
2. Navigate to the "Weave" section
3. View:
   - **Prompts**: Original and optimized prompt versions
   - **Datasets**: Training/validation dataset versions
   - **Traces**: All LLM calls with input/output, tokens, costs

## Example Configuration Files

### Minimal Weave Configuration
```yaml
# configs/facility-with-weave.yaml
system_prompt:
  file: "prompt.txt"
  inputs: ["question"]  
  outputs: ["answer"]

dataset:
  path: "dataset.json"
  input_field: "question"
  golden_output_field: "answer"

model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"

weave:
  enabled: true
  project_name: "my-optimization-project"
```

### Advanced Weave Configuration
```yaml
weave:
  enabled: true
  project_name: "advanced-llama-optimization"
  entity: "my-team"
  # Note: Additional Weave settings can be added here as the integration evolves
```

## What Gets Tracked

### 1. Prompt Evolution 📝
- **Original Prompt**: The initial system prompt before optimization
- **Optimized Prompt**: The final optimized prompt after MIPROv2
- **Versioning**: Both prompts are stored with the same name, creating automatic versions (v1, v2, etc.)
- **Metadata**: Optimization strategy and performance metrics

### 2. Dataset Versions 📊
- **Training Data**: Complete training dataset with metadata
- **Validation Data**: Validation split with size and structure info
- **Test Data**: Test dataset if provided
- **Format Preservation**: Maintains original data structure and field mappings

### 3. LLM Call Traces 🔍
- **Automatic Tracing**: All LLM calls are automatically traced (no code changes needed)
- **Input/Output**: Complete prompt and response pairs
- **Metadata**: Model name, token usage, latency, costs
- **Hierarchical Traces**: Nested calls during optimization process

## CLI Options

```bash
# View all migration options including Weave
llama-prompt-ops migrate --help

# Examples:
llama-prompt-ops migrate --config config.yaml --weave                    # Enable Weave
llama-prompt-ops migrate --config config.yaml --no-weave                 # Disable Weave  
llama-prompt-ops migrate --config config.yaml                            # Use config setting
```

## Configuration Priority

Weave settings are resolved in this order (highest to lowest priority):
1. CLI flags (`--weave` / `--no-weave`)
2. YAML config file (`weave.enabled`)
3. Default (disabled)

## Troubleshooting

### Weave Not Available
```
Warning: Weave not available. Install with: pip install weave
```
**Solution**: Install Weave dependency
```bash
pip install weave>=0.51.0
```

### Authentication Issues
```
Warning: Failed to initialize Weave tracker: [auth error]
```
**Solution**: Login to W&B
```bash
wandb login
```

### Project Not Found
```
Warning: Failed to initialize Weave tracker: Project not found
```
**Solution**: Ensure your W&B entity and project name are correct in the config

### Graceful Degradation
If Weave fails to initialize, the tool continues without tracking:
```
Weave tracking disabled
Starting prompt optimization...
```

## Best Practices

### 1. Project Naming
- Use descriptive project names: `llama-3-optimization-v2`
- Include model family: `llama-70b-facility-qa`
- Add date for time series: `prompt-opt-2024-01`

### 2. Entity Organization
- Use team entities for shared projects
- Personal entities for experiments
- Consistent naming across projects

### 3. Configuration Management
- Keep Weave settings in config files for reproducibility
- Use CLI overrides for quick experiments
- Document project structure in README

### 4. Data Privacy
- Be mindful of sensitive data in prompts/datasets
- Use appropriate W&B privacy settings
- Consider on-premises W&B deployments for sensitive data

## API Reference

### WeaveTracker Class

The core integration class (primarily used internally):

```python
from llama_prompt_ops.integrations import WeaveTracker

# Initialize tracker
tracker = WeaveTracker(
    project_name="my-project",
    entity="my-entity",
    enabled=True
)

# Track prompt evolution (used automatically by CLI)
tracker.track_prompt_evolution(
    original_prompt="Original text",
    optimized_prompt="Optimized text", 
    prompt_name="system_prompt"
)

# Track datasets (used automatically by CLI)
tracker.track_dataset(dataset, split="train")

# Check if tracking is enabled
if tracker.is_enabled():
    print("Weave tracking active")
```

### Configuration Schema

```yaml
weave:
  enabled: boolean              # Enable/disable Weave tracking
  project_name: string         # W&B Weave project name
  entity: string | null        # W&B entity/team (optional)
```

## Integration Details

### Architecture
- **Minimal Dependencies**: Only adds Weave when needed
- **Graceful Degradation**: Continues without tracking if Weave unavailable
- **Native Weave Classes**: Uses `weave.StringPrompt` and `weave.Dataset`
- **Automatic LLM Tracing**: Leverages `weave.init()` for automatic call tracing

### Performance Impact
- **Negligible Overhead**: Weave tracking adds minimal latency
- **Async Operations**: Background uploads don't block optimization
- **Efficient Storage**: Only stores essential data and references

### Security
- **Optional Feature**: Easily disabled for sensitive environments
- **Standard W&B Security**: Inherits W&B's security model
- **No Additional Secrets**: Uses existing W&B authentication

## Support

For issues specific to Weave integration:
1. Check this documentation
2. Verify Weave and W&B setup
3. Test with simple configuration
4. Create issue with reproduction steps

For general llama-prompt-ops issues:
- See main project README
- Check existing GitHub issues
- Create new issue with details