"""
Configuration mappings and settings for the backend API.
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Available models - format: provider/model (e.g., openrouter/meta-llama/...)
MODEL_MAPPING = {
    "Llama 3.3 70B": "openrouter/meta-llama/llama-3.3-70b-instruct",
    "Llama 3.1 8B": "openrouter/meta-llama/llama-3.1-8b-instruct",
    "Llama 3.1 70B": "openrouter/meta-llama/llama-3.1-70b-instruct",
    "GPT-4o": "openai/gpt-4o",
    "GPT-4o-mini": "openai/gpt-4o-mini",
}

# Available metrics from llama-prompt-ops
METRIC_MAPPING = {
    "exact_match": {
        "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
        "params": {"output_field": "answer"},
    },
    "semantic_similarity": {
        "class": "llama_prompt_ops.core.metrics.DSPyMetricAdapter",
        "params": {
            "signature_name": "similarity",
            "score_range": (1, 10),
            "normalize_to": (0, 1),
        },
    },
    "correctness": {
        "class": "llama_prompt_ops.core.metrics.DSPyMetricAdapter",
        "params": {
            "signature_name": "correctness",
            "score_range": (1, 10),
            "normalize_to": (0, 1),
        },
    },
    "json_structured": {
        "class": "llama_prompt_ops.core.metrics.StandardJSONMetric",
        "params": {
            "output_field": "answer",
            "evaluation_mode": "selected_fields_comparison",
            "strict_json": False,
        },
    },
    # Legacy mappings for backward compatibility
    "Facility Support": {
        "class": "llama_prompt_ops.core.metrics.FacilityMetric",
        "params": {"output_field": "answer", "strict_json": False},
    },
    "HotpotQA": {
        "class": "llama_prompt_ops.datasets.hotpotqa.HotpotQAMetric",
        "params": {"output_field": "answer"},
    },
    "Standard JSON": {
        "class": "llama_prompt_ops.core.metrics.StandardJSONMetric",
        "params": {"output_field": "answer"},
    },
    "Exact Match": {
        "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
        "params": {},
    },
}

# Available dataset adapters from llama-prompt-ops
DATASET_ADAPTER_MAPPING = {
    "standard_json": {
        "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "description": "Standard JSON format with customizable field mappings",
        "example_fields": {"input": "string", "output": "string"},
        "params": {"input_field": "input", "golden_output_field": "output"},
    },
    "hotpotqa": {
        "adapter_class": "llama_prompt_ops.datasets.hotpotqa.adapter.HotPotQAAdapter",
        "description": "Multi-hop reasoning dataset for question answering",
        "example_fields": {
            "question": "string",
            "answer": "string",
            "context": "array",
        },
        "params": {
            "input_field": "question",
            "golden_output_field": "answer",
            "context_field": "context",
        },
    },
    "facility": {
        "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "description": "Facility support and maintenance dataset with nested field structure",
        "example_fields": {"fields": "object", "answer": "string"},
        "params": {
            # Nested path for facility dataset
            "input_field": ["fields", "input"],
            "golden_output_field": "answer",
        },
    },
}

# Available optimization strategies from llama-prompt-ops
STRATEGY_MAPPING = {
    "Basic": "basic",
}

# System message for OpenRouter operations
ENHANCE_SYSTEM_MESSAGE = """
    You are a highly advanced language model, capable of complex reasoning and problem-solving.
    Your goal is to provide accurate and informative responses to the given input, following a    structured approach.
            Here is the input you'll work with:
            <INPUT>
            {{USER_INPUT}}
            </INPUT>
            To accomplish this, follow these steps:
            Understand the Task: Carefully read and comprehend the input, identifying the key elements and requirements.
            Break Down the Problem: Decompose the task into smaller, manageable sub-problems, using a chain-of-thought (CoT) approach.
            Gather Relevant Information: If necessary, use external knowledge sources to gather relevant information and provide provenance for your answers.
            Apply Reasoning and Logic: Apply step-by-step reasoning and logical thinking to arrive at a solution, using self-ask prompting to guide your thought process.
            Evaluate and Refine: Evaluate your solution, refining it as needed to ensure accuracy and completeness.
            Your output must follow these guidelines:
            Clear and Concise: Provide clear and concise responses, avoiding ambiguity and jargon.
            Well-Structured: Use a well-structured format for your response, including headings and bullet points as needed.
            Accurate and Informative: Ensure that your response is accurate and informative, providing relevant details and examples.
            Format your final answer inside <OUTPUT> tags and do not include any of your internal reasoning.
            <OUTPUT>
            ...your response...
            </OUTPUT>
            Chain of Thought (CoT) Template
            To facilitate CoT, use the following template:
            Step 1: Identify the key elements and requirements of the task.
            Sub-question: What are the essential components of the task?
            Answer: [Provide a brief answer]
            Step 2: Break down the problem into smaller sub-problems.
            Sub-question: How can I decompose the task into manageable parts?
            Answer: [Provide a brief answer]
            Step 3: Gather relevant information and apply reasoning and logic.
            Sub-question: What information do I need to solve the task, and how can I apply logical thinking?
            Answer: [Provide a brief answer]
            Step 4: Evaluate and refine the solution.
            Sub-question: Is my solution accurate and complete, and how can I refine it?
            Answer: [Provide a brief answer]
            By following this structured approach, you will be able to provide accurate and informative responses to the given input, demonstrating your ability to think critically and solve complex problems."""

# ==============================================================================
# APPLICATION SETTINGS
# ==============================================================================
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploaded_datasets")

# Behavior
FAIL_ON_ERROR = (
    False  # If True, raise errors instead of falling back on optimization failure
)
DEBUG_MODE = False

# Model defaults
DEFAULT_MODEL = "openrouter/meta-llama/llama-3.3-70b-instruct"
DEFAULT_TEMPERATURE = 0.0

# Dataset split defaults
DEFAULT_TRAIN_SIZE = 0.7
DEFAULT_VAL_SIZE = 0.15
