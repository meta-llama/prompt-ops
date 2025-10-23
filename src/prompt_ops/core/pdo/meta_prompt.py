# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Centralized meta prompt templates for PDO.

This module contains all user-facing prompt templates used by the optimization
engine: dataset summarization, instruction proposal, task prompting, judging,
and mutation prompting.
"""


# Prompt templates for instruction generation and mutation (dataset summary + proposer)
DATASET_DESCRIPTOR_PROMPT = """
You are a data analyst specialized in preparing instructions for language models.

Your task is to write a **clear, structured summary** of the unlabeled dataset based on the sample inputs provided below.

## Sample Unlabeled Inputs ##
{examples}

## Summary Guidelines ##
- Focus on input structure: Is it plain text, question-answer pairs, JSON dictionaries, CSV rows, lists, etc.?
- Identify common data fields, phrasing patterns, or key terminology present across examples.
- Describe typical input length (short phrases, single sentences, multi-step reasoning questions, etc.).
- Mention any domain-specific jargon, numbers, or named entities if present.
- Do **not** attempt to infer answers, labels, or outputs.
- Keep the summary concise: 3 to 5 sentences total.

## Your Output ##
Write a concise natural-language summary of the dataset's input characteristics, suitable for guiding an instruction proposal system.
"""


INSTRUCTION_PROPOSER_TEMPLATE = """
You are an expert prompt‑engineer.
Your task is to generate **exactly 1** *high‑quality* **system‑level instruction** for the target reasoning task.

# Dataset Snapshot
Below is an *LM‑written summary* of the unlabeled question pool:
{dataset_summary}

# Sample Inputs (do NOT answer them)
{questions}

# Prompt‑Engineering Tip
{tip}

# Length & Style Constraints
- Avoid dataset‑specific jargon unless it appears in the sample inputs.
- Vary phrasing and level of explicit reasoning to foster exploration.

# Output Format (STRICT)
Return **exactly** 1 item in a JSON array, *and nothing else*:

[
"Your single high-quality instruction here"
]
"""


# Task response prompt template enforcing structured JSON
REASON_PROMPT = """
## Instruction ##
{instruction}

## Question ##
{question}

## Output format ##
You must follow the instruction exactly as given above. Provide a brief reasoning for your answer, then select one of the following choices: {answer_choices_str}. Your response must be returned strictly in the following JSON format, with no additional text:

{{
  "reasoning": "Brief explanation of your reasoning (1-2 sentences)",
  "answer": "{answer_choices_str}"
}}

Do not include any explanation or extra output outside the JSON.
"""


# Evaluation prompt template (consumes structured task outputs)
EVALUATE_PROMPT = """
## Role ##
You are a meticulous, impartial referee evaluating two competing responses to determine which better satisfies the given task.

## Task ##
{question}

## Response from Prompt X ##
**Reasoning:** {reasoning_X}
**Answer:** {answer_X}

## Response from Prompt Y ##
**Reasoning:** {reasoning_Y}
**Answer:** {answer_Y}

## Evaluation Criteria ##
Evaluate both responses using the following weighted criteria:

1. **Correctness (50%)** - Does the final answer match factual reality and task requirements?
2. **Reasoning Quality (50%)** - Is the logic coherent, complete, and free of hallucinations?

## Output Instructions ##
- Provide detailed justification for your decision (~100 words)
- Select the winner: either "X" or "Y"
- Output **only** the JSON object below with **no additional text**

## Output Format ##
{{
  "reasoning": "Your detailed justification explaining why prompt X or Y produced the better response (~100 words).",
  "winner": "X or Y"
}}
"""


# Evaluation schema for judge JSON output
EVALUATE_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "winner": {"type": "string", "enum": ["X", "Y"]},
    },
    "required": ["reasoning", "winner"],
    "additionalProperties": False,
}


# Helper to build task JSON schema given dynamic answer choices
def get_reason_schema(answer_choices):
    return {
        "type": "object",
        "properties": {
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of the reasoning behind the answer",
            },
            "answer": {
                "type": "string",
                "enum": answer_choices,
                "description": "The selected answer choice",
            },
        },
        "required": ["reasoning", "answer"],
        "additionalProperties": False,
    }


# Initial instruction tips used during seed generation
INITIAL_INSTRUCTION_TIPS = {
    "framing": "Set the context for the task by framing it as a concrete creative scenario.",
    "simple": "Keep the instruction clear and concise.",
    "description": "Make sure your instruction is very informative and descriptive.",
    "persona": "Provide the LM with a creative persona that is relevant to the task.",
    "edge_cases": "List tricky cases the instruction must handle.",
    "assumptions": "Have the model state assumptions before solving.",
}

# Mutation tips and templates
MUTATION_TIPS = {
    "expansion": "Keep the current champion instruction exactly as is, but expand on it by adding additional helpful guidance or clarifications. The result should be the original instruction plus new supplementary content.",
    "minimal": "Make very minimal changes to the current champion instruction. Keep it around the same length and modify only a few words through paraphrasing while preserving the core meaning.",
    "few_shot": "Add a few concrete examples to the current champion instruction to demonstrate the expected reasoning process or output format. Include 1-3 brief example cases that show how to apply the instruction.",
    "emphasis": "Adjust the tone, emphasis, or directional focus of the current champion instruction to create different reasoning patterns.",
}

MUTATE_PROMPT_TEMPLATE = """
You are an expert prompt‑engineer specializing in prompt optimization.
Your task is to generate 1 *diverse, high‑quality* **mutation** of the currently **BEST PERFORMING** instruction for the target reasoning task.

# BEST PERFORMING Instruction (Current Champion)
{instructions}

# CRITICAL: Follow This Prompt‑Engineering Tip
{tip}

# Output Format
Return **exactly** 1 mutated instruction in a JSON object, *and nothing else*:

{{
  "mutated_prompt": "Your mutated instruction here, following the tip."
}}
"""

MUTATE_PROMPT_TEMPLATE_WITH_LABELS = """
You are an expert prompt‑engineer specializing in prompt optimization.
Your task is to generate 1 *diverse, high‑quality* **mutation** of the currently **BEST PERFORMING** instruction for the target reasoning task.

# BEST PERFORMING Instruction (Current Champion)
{instructions}

# 📘 Sample Input-Output Pairs (for context)
{sample_pairs}

# CRITICAL: Follow This Prompt‑Engineering Tip
{tip}

# Output Format
Return **exactly** 1 mutated instruction in a JSON object, *and nothing else*:

{{
  "mutated_prompt": "Your mutated instruction here, following the tip."
}}
"""
