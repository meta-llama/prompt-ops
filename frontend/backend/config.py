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

# Available metrics from prompt-ops
METRIC_MAPPING = {
    "exact_match": {
        "class": "prompt_ops.core.metrics.ExactMatchMetric",
        "params": {"output_field": "answer"},
    },
    "semantic_similarity": {
        "class": "prompt_ops.core.metrics.DSPyMetricAdapter",
        "params": {
            "signature_name": "similarity",
            "score_range": (1, 10),
            "normalize_to": (0, 1),
        },
    },
    "correctness": {
        "class": "prompt_ops.core.metrics.DSPyMetricAdapter",
        "params": {
            "signature_name": "correctness",
            "score_range": (1, 10),
            "normalize_to": (0, 1),
        },
    },
    "json_structured": {
        "class": "prompt_ops.core.metrics.StandardJSONMetric",
        "params": {
            "output_field": "answer",
            "evaluation_mode": "selected_fields_comparison",
            "strict_json": False,
        },
    },
    # Legacy mappings for backward compatibility
    "Facility Support": {
        "class": "prompt_ops.core.metrics.FacilityMetric",
        "params": {"output_field": "answer", "strict_json": False},
    },
    "HotpotQA": {
        "class": "prompt_ops.datasets.hotpotqa.HotpotQAMetric",
        "params": {"output_field": "answer"},
    },
    "Standard JSON": {
        "class": "prompt_ops.core.metrics.StandardJSONMetric",
        "params": {"output_field": "answer"},
    },
    "Exact Match": {
        "class": "prompt_ops.core.metrics.ExactMatchMetric",
        "params": {},
    },
}

# Available dataset adapters from prompt-ops
DATASET_ADAPTER_MAPPING = {
    "standard_json": {
        "adapter_class": "prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "description": "Standard JSON format with customizable field mappings",
        "example_fields": {"input": "string", "output": "string"},
        "params": {"input_field": "input", "golden_output_field": "output"},
    },
    "hotpotqa": {
        "adapter_class": "prompt_ops.datasets.hotpotqa.adapter.HotPotQAAdapter",
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
        "adapter_class": "prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "description": "Facility support and maintenance dataset with nested field structure",
        "example_fields": {"fields": "object", "answer": "string"},
        "params": {
            # Nested path for facility dataset
            "input_field": ["fields", "input"],
            "golden_output_field": "answer",
        },
    },
}

# Available optimization strategies from prompt-ops
STRATEGY_MAPPING = {
    "Basic": "basic",
}

# System prompt for prompt enhancement
ENHANCE_SYSTEM_PROMPT = """
    # Expert System Prompt Engineer

    You are a specialist in crafting high-quality system prompts that produce consistent AND effective AI outputs. You transform task descriptions into clear AND structured instructions.

    ## Input Processing

    You will receive:
    - **Task Description** (required): What the user wants the model to do
    - **Current System Prompt** (optional): An existing prompt to optimize

    ## Your Optimization Process

    ### Phase 1: UNDERSTAND THE REQUIREMENTS

    **If current prompt exists:**
    - Analyze its structure, strengths, and weaknesses
    - Identify what's working well to preserve
    - Spot ambiguities, contradictions, or missing elements

    **For the task description:**
    - Extract the core objective and key requirements
    - Identify implied constraints and success criteria
    - Determine complexity level and domain

    ### Phase 2: DETERMINE APPROACH

    **Enhancement Mode** (when current prompt exists and is strong):
    - Preserve effective structure and instructions
    - Make targeted improvements for clarity
    - Add missing constraints or examples
    - Refine organization and formatting

    **Creation Mode** (when starting fresh or current prompt is weak):
    - Build comprehensive structure from scratch
    - Apply full optimization framework
    - Create clear role, process, and output specifications

    ### Phase 3: APPLY OPTIMIZATION PRINCIPLES

    **1. Structure & Clarity**
    - Use markdown headers, bullets, and formatting for scannability
    - Organize logically: Role → Task → Process → Output Format → Constraints
    - Group related instructions together
    - Use emphasis (**bold**, *italic*) for critical points

    **2. Eliminate Ambiguity**
    - Replace vague language ("try to", "maybe", "if possible") with concrete directives
    - Remove contradictions between instructions
    - Distinguish between requirements (must) and preferences (should)
    - Define technical terms and domain-specific concepts

    **3. Provide Clear Guidance**
    - Include step-by-step reasoning for complex tasks
    - Specify how to handle edge cases and exceptions
    - Give decision-making criteria when choices are involved
    - Add examples that demonstrate both process and output

    **4. Define Success Criteria**
    - Specify exact output format with structure and constraints
    - State behavioral priorities (accuracy, tone, completeness, etc.)
    - Include quality standards and validation checks
    - Show complete examples of desired outputs

    **5. Behavioral Instructions**
    - Define the AI's role, persona, or expertise clearly
    - Specify tone, style, and communication approach
    - Set boundaries for what the AI should/shouldn't do
    - Include error handling and uncertainty management

    ### Phase 4: QUALITY CHECKLIST

    Before finalizing, verify:
    - [ ] Core objective is crystal clear
    - [ ] All requirements are actionable and specific
    - [ ] Output format is precisely defined
    - [ ] Edge cases and constraints are addressed
    - [ ] Examples demonstrate complete reasoning
    - [ ] No conflicting instructions exist
    - [ ] Structure is logical and scannable
    - [ ] Technical terms are defined

    Remember: A great prompt is **straightforward, specific, and well-structured**. It should enable consistent, high-quality outputs while being maintainable and easy to understand.

    ## Required Output Format

    You must return **only** the optimized prompt and nothing else."""

# ==============================================================================
# APPLICATION SETTINGS
# ==============================================================================
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploaded_datasets")

# Server settings
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))

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
