# Quick Start Guide: Optimizing Prompts for Llama Models

## Example Use Case: Customer Service Message Classification

In this guide, we'll optimize a prompt for classifying customer service messages in a facility management context. The task involves extracting three key pieces of information:
- **Urgency**: high, medium, or low
- **Sentiment**: positive, neutral, or negative
- **Categories**: relevant service categories from a predefined list

## Step 1: Original System Prompt

Here's our starting prompt that we want to optimize:

```
You are a helpful assistant. Extract and return a json with the follwoing keys and values:
- "urgency" as one of `high`, `medium`, `low`
- "sentiment" as one of `negative`, `neutral`, `positive`
- "categories" Create a dictionary with categories as keys and boolean values (True/False), where the value indicates whether the category is one of the best matching support category tags from: `emergency_repair_services`, `routine_maintenance_requests`, `quality_and_safety_concerns`, `specialized_cleaning_services`, `general_inquiries`, `sustainability_and_environmental_practices`, `training_and_support_requests`, `cleaning_services_scheduling`, `customer_feedback_and_complaints`, `facility_management_issues`
Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. Never enclose it in ```json...```, no newlines, no unnessacary whitespaces.
```

## Step 2: Create a Simple Configuration File

Create a file named `facility-simple.yaml` with the following content:

```yaml
# Core configuration
prompt:
  file: "../dataset/facility-synth/facility_prompt_sys.txt"
  inputs: ["question"]
  outputs: ["answer"]

# Dataset configuration
dataset:
  path: "../dataset/facility-synth/facility_v2_test.json"
  input_field: ["fields", "input"]
  golden_output_field: "answer"

# Model configuration
model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"

# Metric configuration
metric:
  class: "standard_json"
  evaluation_mode: "flattened"
  fields: ["urgency", "sentiment", "categories"]
  required_fields: ["urgency", "sentiment", "categories"]

# Optimization settings
optimization:
  strategy: "basic"
```

## Step 3: Run the Optimization

```bash
# Install the package
pip install -e .

# Set your API key (choose the appropriate one for your llama provider)
export OPENROUTER_API_KEY=your_key_here
# OR
# export TOGETHER_API_KEY=your_key_here

# Run the optimization
prompt-ops migrate --config configs/facility-simple.yaml
```

## Step 4: Review the Optimized Prompt

The optimized prompt will be saved in the `results/` directory with a filename including "facility-simple" and a timestamp. It will include:

1. An improved system prompt
2. Few-shot examples to help the model understand the task better
3. Performance metrics comparing the original and optimized prompts

Here's what an optimized prompt looks like:

```yaml
system: |-
    <s>[INST] You are a helpful assistant. Extract and return a json with the follwoing keys and values:
    - "urgency" as one of `high`, `medium`, `low`
    - "sentiment" as one of `negative`, `neutral`, `positive`
    - "categories" Create a dictionary with categories as keys and boolean values (True/False), where the value indicates whether the category is one of the best matching support category tags from: `emergency_repair_services`, `routine_maintenance_requests`, `quality_and_safety_concerns`, `specialized_cleaning_services`, `general_inquiries`, `sustainability_and_environmental_practices`, `training_and_support_requests`, `cleaning_services_scheduling`, `customer_feedback_and_complaints`, `facility_management_issues`
    Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. Never enclose it in ```json...```, no newlines, no unnessacary whitespaces.
     [/INST]
    
    Follow these instruction formats:
    1. For reasoning tasks, use numbered steps with explicit state tracking: '1. Current Information: [list facts] 2. Analysis Needed: [list questions] 3. Steps to Answer: [list steps] 4. Conclusion: [summarize findings]'
    2. Use explicit chain-of-thought reasoning: 'Given [X], I think [Y] because [Z]. This leads to [conclusion] for these reasons: [1,2,3]'. Example: 'Given the function uses recursion, I think we should add a base case because infinite recursion is possible.'
    3. For validation tasks, enforce this pattern: 'TEST: [description] -> EXPECTED: [outcome] -> ACTUAL: [result] -> PASS/FAIL: [status] -> FIX: [if needed]'

    Few-shot examples:

    Example 1:
        Question: [Customer message example]
        Answer: {"urgency": "medium", "sentiment": "neutral", "categories": {"training_and_support_requests": true, ...}}
```

## Next Steps

1. **Use the optimized prompt** in your production system
2. **Try different optimization strategies** (light, medium, heavy)
3. **Customize the configuration** for your specific use case

For a detailed guide on all configuration options, check out the [Advanced Facility Configuration Guide](/examples/advanced/advanced_facility_config.md) which explains each setting in depth.
