# Quick Start Guide: Optimizing Prompts in 5 Minutes

## What You'll Build

In this quick guide, you'll optimize a prompt for classifying customer service messages with just a few commands. The system will extract:

- **Urgency**: high, medium, or low
- **Sentiment**: positive, neutral, or negative
- **Categories**: relevant service categories from a predefined list

You can explore the complete dataset and prompt in the `use-cases/facility-support-analyzer` directory, which contains the sample data and system prompts used in this guide.

## Step 1: Installation

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/meta-llama/prompt-ops.git
# or with ssh
# git clone git@github.com:meta-llama/prompt-ops.git
cd prompt-ops

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode
pip install -e .
```

## Step 2: Create a sample project

This will create a directory called my-project with a sample configuration and dataset in the current folder.

```bash
llama-prompt-ops create my-project
cd my-project
```

## Step 3: Set Up Your API Key

Add your API key to the `.env` file:

```bash
OPENROUTER_API_KEY=your_key_here
```

You can get an OpenRouter API key by creating an account at [OpenRouter](https://openrouter.ai/). For more inference provider options, see [Inference Providers](../inference_providers.md).

## Step 4: Run Optimization

```bash
llama-prompt-ops migrate # defaults to config.yaml if --config not specified
```

Done! The optimized prompt will be saved to the `results` directory with performance metrics comparing the original and optimized versions.

## Example Output

The optimized prompt will be saved in the `results/` directory with a filename like `facility-simple_YYYYMMDD_HHMMSS.yaml`. When you open this file, you'll see something like this:

````yaml
system: |-
Analyze the customer's message and determine the level of urgency, sentiment, and relevant categories. Extract and return a json with the keys "urgency", "sentiment", and "categories". The "urgency" key should have a value of "high", "medium", or "low", the "sentiment" key should have a value of "negative", "neutral", or "positive", and the "categories" key should have a dictionary with categories as keys and boolean values indicating whether the category is a best matching support category tag. The categories should include "emergency_repair_services", "routine_maintenance_requests", "quality_and_safety_concerns", "specialized_cleaning_services", "general_inquiries", "sustainability_and_environmental_practices", "training_and_support_requests", "cleaning_services_scheduling", "customer_feedback_and_complaints", and "facility_management_issues".

  Few-shot examples:

  Example 1:
      Question: Our office bathroom needs cleaning urgently. The toilets are clogged and there's water on the floor.
      Answer: {"urgency": "high", "sentiment": "negative", "categories": {"emergency_repair_services": true, "specialized_cleaning_services": true, "facility_management_issues": true, "emergency_repair_services": false, "routine_maintenance_requests": false, "quality_and_safety_concerns": false, "general_inquiries": false, "sustainability_and_environmental_practices": false, "training_and_support_requests": false, "customer_feedback_and_complaints": false}}
````

## Next Steps

**Explore our intermediate [Facility Configuration Guide](../intermediate/README.md)** to learn about advanced configuration options including custom model settings, dataset parameters, and fine-tuning the FacilityMetric for better evaluation
