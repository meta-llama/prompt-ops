# Quick Start Guide: Optimizing Prompts in 5 Minutes

## What You'll Build

In this quick guide, you'll optimize a prompt for classifying customer service messages with just a few commands. The system will extract:

- **Urgency**: high, medium, or low
- **Sentiment**: positive, neutral, or negative
- **Categories**: relevant service categories from a predefined list

You can explore the complete dataset and prompt in the `use-cases/facility-synth` directory, which contains the sample data and system prompts used in this guide.

## Step 1: Install prompt-ops

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/meta-llama/prompt-ops.git
# or with ssh
# git clone git@github.com:meta-llama/prompt-ops.git
cd prompt-ops

# Install the package in development mode
pip install -e .
```

## Step 2: Create Configuration File

Run this command to create a basic configuration file:

````bash
# Create configs directory if it doesn't exist
mkdir -p configs

# Create the configuration file
cat > configs/facility-simple.yaml << 'EOL'
prompt:
  text: |
    You are a helpful assistant. Extract and return a json with the following keys and values:
    - "urgency" as one of `high`, `medium`, `low`
    - "sentiment" as one of `negative`, `neutral`, `positive`
    - "categories" Create a dictionary with categories as keys and boolean values (True/False), where the value indicates whether the category is one of the best matching support category tags from: `emergency_repair_services`, `routine_maintenance_requests`, `quality_and_safety_concerns`, `specialized_cleaning_services`, `general_inquiries`, `sustainability_and_environmental_practices`, `training_and_support_requests`, `cleaning_services_scheduling`, `customer_feedback_and_complaints`, `facility_management_issues`
    Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. Never enclose it in ```json...```, no newlines, no unnessacary whitespaces.
  inputs: ["question"]
  outputs: ["answer"]

# Dataset configuration
dataset:
  path: "../use-cases/facility-synth/facility_v2_test.json"
  input_field: ["fields", "input"]
  golden_output_field: "answer"

# Model configuration
model:
  name: "openrouter/meta-llama/llama-3.3-70b-instruct"

# Metric configuration
metric:
  class: "prompt_ops.core.metrics.FacilityMetric"
  strict_json: false
  output_field: "answer"

# Optimization settings
optimization:
  strategy: "llama"
EOL
````

## Step 3: Set Up Your API Key

Create a `.env` file in the project root with your API key:

```bash
# Create a .env file with your API key
echo "OPENROUTER_API_KEY=your_key_here" > .env
```

The prompt-ops tool will automatically load this file when running.

## Step 4: Run the Optimization

```bash
# Run the optimization
prompt-ops migrate --config configs/facility-simple.yaml
```

That's it! The optimized prompt will be saved in the `results/` directory with a filename including "facility-simple" and a timestamp.

## Example Output

The optimized prompt will be saved in the `results/` directory with a filename like `facility-simple_YYYYMMDD_HHMMSS.yaml`. When you open this file, you'll see something like this:

````yaml
system: |-
  You are a helpful assistant. Extract and return a json with the following keys and values:
  - "urgency" as one of `high`, `medium`, `low`
  - "sentiment" as one of `negative`, `neutral`, `positive`
  - "categories" Create a dictionary with categories as keys and boolean values (True/False), where the value indicates whether the category is one of the best matching support category tags from: `emergency_repair_services`, `routine_maintenance_requests`, `quality_and_safety_concerns`, `specialized_cleaning_services`, `general_inquiries`, `sustainability_and_environmental_practices`, `training_and_support_requests`, `cleaning_services_scheduling`, `customer_feedback_and_complaints`, `facility_management_issues`
  Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. Never enclose it in ```json...```, no newlines, no unnessacary whitespaces.

  Few-shot examples:

  Example 1:
      Question: Our office bathroom needs cleaning urgently. The toilets are clogged and there's water on the floor.
      Answer: {"urgency": "high", "sentiment": "negative", "categories": {"emergency_repair_services": true, "specialized_cleaning_services": true, "facility_management_issues": true, "emergency_repair_services": false, "routine_maintenance_requests": false, "quality_and_safety_concerns": false, "general_inquiries": false, "sustainability_and_environmental_practices": false, "training_and_support_requests": false, "customer_feedback_and_complaints": false}}
````

## Next Steps

**Explore our intermediate [Facility Configuration Guide](../intermediate/README.md)** to learn about advanced configuration options including custom model settings, dataset parameters, and fine-tuning the FacilityMetric for better evaluation
