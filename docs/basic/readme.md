# Quick Start Guide: Optimizing Prompts in 5 Minutes

## What You'll Build

In this quick guide, you'll optimize a prompt for classifying customer service messages with just a few commands. The system will extract:

- **Urgency**: high, medium, or low
- **Sentiment**: positive, neutral, or negative
- **Categories**: relevant service categories from a predefined list

You can explore the complete dataset and prompt in the `use-cases/facility-support-analyzer` directory, which contains the sample data and system prompts used in this guide.

## Understanding the Facility Support Analyzer

Before diving into the installation, let's take a closer look at the components of this use case. You can find all the relevant files in the [`use-cases/facility-support-analyzer`](../../use-cases/facility-support-analyzer/) directory:

- [`facility_prompt_sys.txt`](../../use-cases/facility-support-analyzer/facility_prompt_sys.txt) - System prompt for the task
- [`facility_v2_test.json`](../../use-cases/facility-support-analyzer/facility_v2_test.json) - Dataset with customer service messages
- [`facility-simple.yaml`](../../use-cases/facility-support-analyzer/facility-simple.yaml) - Simple configuration file
- [`eval.ipynb`](../../use-cases/facility-support-analyzer/eval.ipynb) - Evaluation notebook

### Existing System Prompt

The system prompt instructs the LLM to analyze customer service messages and extract structured information in JSON format:

```
You are a helpful assistant. Extract and return a json with the following keys and values:
- "urgency" as one of `high`, `medium`, `low`
- "sentiment" as one of `negative`, `neutral`, `positive`
- "categories" Create a dictionary with categories as keys and boolean values (True/False), where the value indicates whether the category is one of the best matching support category tags from: `emergency_repair_services`, `routine_maintenance_requests`, `quality_and_safety_concerns`, `specialized_cleaning_services`, `general_inquiries`, `sustainability_and_environmental_practices`, `training_and_support_requests`, `cleaning_services_scheduling`, `customer_feedback_and_complaints`, `facility_management_issues`
Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. Never enclose it in ```json...```, no newlines, no unnessacary whitespaces.
```

### Dataset Format

The dataset consists of customer service messages in JSON format. Each entry contains:

1. An input field with the customer's message (typically an email or support ticket)
2. An answer field with the expected JSON output containing urgency, sentiment, and categories

Example entry:

```json
{
  "fields": {
    "input": "Subject: Urgent HVAC Repair Needed\n\nHi ProCare Support Team,\n\nI'm reaching out with an urgent issue that needs immediate attention. Our HVAC system has been acting up for the past two days, and it's starting to affect the comfort of our living space. I've tried resetting the system and checking the filters, but nothing seems to work.\n\nCould you please send someone over as soon as possible?\n\nThank you,\n[Sender]"
  },
  "answer": "{\"categories\": {\"routine_maintenance_requests\": false, \"customer_feedback_and_complaints\": false, \"training_and_support_requests\": false, \"quality_and_safety_concerns\": false, \"sustainability_and_environmental_practices\": false, \"cleaning_services_scheduling\": false, \"specialized_cleaning_services\": false, \"emergency_repair_services\": true, \"facility_management_issues\": false, \"general_inquiries\": false}, \"sentiment\": \"positive\", \"urgency\": \"high\"}"
}
```

### Metric Calculation

The FacilityMetric evaluates the model's outputs by comparing them to the ground truth answers. It checks:

1. **Urgency Classification**: Accuracy in determining if a request is high, medium, or low priority
2. **Sentiment Analysis**: Accuracy in classifying the customer's tone as positive, neutral, or negative
3. **Category Tagging**: Precision and recall in identifying the correct service categories

The metric parses both the predicted and ground truth JSON outputs, compares them field by field, and calculates an overall score that reflects how well the model is performing on this task.


## Step 1: Installation

```bash
# Create a virtual environment
conda create -n prompt-ops python=3.10
conda activate prompt-ops

# Install from PyPI
pip install prompt-ops

# OR install from source
git clone https://github.com/meta-llama/prompt-ops.git
cd prompt-ops
pip install -e .

```
## Step 2: Create a sample project

By default this will create the necessary sample files for Facility Support Analyzer in the current directory called my-project.

```bash
prompt-ops create my-project
cd my-project
```


### Output
The directory will be created with a sample configuration and dataset in the current folder.

```
my-project
├── .env
├── README.md
├── config.yaml
├── data
│   └── dataset.json
├── prompts
│   └── prompt.txt
└── results
```


## Step 3: Set Up Your API Key

Add your API key to the `.env` file:

```bash
OPENROUTER_API_KEY=your_key_here
```

You can get an OpenRouter API key by creating an account at [OpenRouter](https://openrouter.ai/). For more inference provider options, see [Inference Providers](../inference_providers.md).

## Step 4: Run Optimization

```bash
prompt-ops migrate # defaults to config.yaml if --config not specified
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

**Explore our intermediate [Facility Configuration Guide](../intermediate/readme.md)** to learn about advanced configuration options including custom model settings, dataset parameters, and fine-tuning the FacilityMetric for better evaluation
