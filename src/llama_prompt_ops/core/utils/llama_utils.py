# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Llama-specific prompt optimization utilities.

This module contains Llama-specific tips, templates, and utilities
for optimizing prompts for Llama models.
"""

from typing import Dict, Any, List, Optional
import random
import re


LLAMA_TIPS = {
    "instruction_preferences": [
        "For complex tasks, always use this format: 'OBSERVE current state -> DECIDE next steps -> EXECUTE action -> VALIDATE results'. Example: 'OBSERVE: User provided a Python function. DECIDE: Code review needed. EXECUTE: Performing review. VALIDATE: No security issues found.'",
        "When calling functions, enforce this structure: '1. Determine need (FN_CALL=True/False) 2. If True, provide complete function signature with docstring 3. Execute function 4. Validate results'. Example: 'FN_CALL=True\ndef process_data(input: str) -> dict: \"\"\"Processes input string to dictionary\"\"\"'",
        "For reasoning tasks, use numbered steps with explicit state tracking: '1. Current Information: [list facts] 2. Analysis Needed: [list questions] 3. Steps to Answer: [list steps] 4. Conclusion: [summarize findings]'",
        "Break down all responses into these sections: '[CONTEXT] -> [ANALYSIS] -> [IMPLEMENTATION] -> [VALIDATION] -> [NEXT STEPS]'. Each section must be explicitly labeled and completed before moving to the next",
        "For error checking, implement this checklist: '□ Input validated □ Types checked □ Edge cases considered □ Output verified □ Side effects documented'. Mark each box when completed",
        "Maintain consistent formatting: Use bullet points for lists, numbered steps for procedures, code blocks for code, and quote blocks for examples. Example: '1. First step\n • Sub-point A\n • Sub-point B\n```python\ncode_example()```'",
        "For context switches, follow: '1. Summarize current state 2. Archive relevant info 3. Clear temporary data 4. Load new context 5. Verify completeness'. Example: 'Current: Code review. Archiving: Security findings. Loading: Performance context.'",
        "Use explicit chain-of-thought reasoning: 'Given [X], I think [Y] because [Z]. This leads to [conclusion] for these reasons: [1,2,3]'. Example: 'Given the function uses recursion, I think we should add a base case because infinite recursion is possible.'",
        "For validation tasks, enforce this pattern: 'TEST: [description] -> EXPECTED: [outcome] -> ACTUAL: [result] -> PASS/FAIL: [status] -> FIX: [if needed]'",
        "When handling cultural or linguistic content, structure as: 'ORIGINAL: [text] -> CULTURAL CONTEXT: [explanation] -> ADAPTATION: [modified version] -> VERIFICATION: [cultural accuracy check]'",
        "For code generation, follow: '1. Requirements analysis 2. Function signature 3. Input validation 4. Core logic 5. Error handling 6. Output validation 7. Documentation 8. Tests'. Each step must be explicitly completed",
        "Use role-based prompting with clear constraints: 'You are [role] with expertise in [domain]. Your task is [specific goal]. Constraints: [list]. Example: 'You are a security auditor with expertise in Python. Your task is to review this authentication code. Constraints: Must follow OWASP guidelines.'",
        "For problem-solving, implement: 'PROBLEM: [clear statement] -> APPROACH: [methodology] -> SOLUTION: [steps] -> VERIFICATION: [tests] -> ALTERNATIVES: [other options]'",
        "When making recommendations, use: 'CURRENT STATE -> ISSUES IDENTIFIED -> PROPOSED CHANGES -> EXPECTED BENEFITS -> IMPLEMENTATION STEPS -> VALIDATION PLAN'",
        "For technical documentation, structure as: 'PURPOSE -> PREREQUISITES -> IMPLEMENTATION -> USAGE EXAMPLES -> COMMON ISSUES -> TROUBLESHOOTING -> MAINTENANCE'",
        "If the task requires the answer to be concise, make sure to include instruction to be very concise and not verbose in the prompt."
    ]
}

LLAMA_TEMPLATES = {
    "basic": "<s>[INST] {instruction} [/INST]",
    "with_context": "<s>[INST] {instruction} [/INST] {context}",
    "with_examples": "<s>[INST] {instruction}\n\nExamples:\n{examples} [/INST]",
    "full": "<s>[INST] {instruction}\n\n{context}\n\nExamples:\n{examples} [/INST]"
}


def is_llama_model(model_name: str) -> bool:
    """
    Check if a model is a Llama model, regardless of provider prefix.
    
    Args:
        model_name: The name of the model
        
    Returns:
        True if the model is a Llama model, False otherwise
    """
    if model_name is None:
        return False
        
    model_name = model_name.lower()
    llama_pattern = r'(^|/)((meta-)?llama)($|[/-])'
    
    return bool(re.search(llama_pattern, model_name))



def get_llama_tips(tip_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Llama-specific tips.
    
    Args:
        tip_type: Optional specific tip type to retrieve
        
    Returns:
        Dictionary of tips or a specific tip if tip_type is provided
    """
    if tip_type:
        return {tip_type: LLAMA_TIPS.get(tip_type, [])}
    return LLAMA_TIPS


def get_llama_template(template_type: str = "basic") -> str:
    """
    Get a prompt template for Llama models.
    
    Args:
        template_type: The type of template to retrieve
        
    Returns:
        Template string for the specified template type
    """
    return LLAMA_TEMPLATES.get(template_type, LLAMA_TEMPLATES["basic"])


def get_task_type_from_prompt(prompt_text: str, input_fields: List[str], output_fields: List[str]) -> str:
    """
    Determine the task type from the prompt text and input/output fields.
    
    Args:
        prompt_text: The prompt text
        input_fields: List of input field names
        output_fields: List of output field names
        
    Returns:
        Task type as a string (e.g., "classification", "generation", "extraction", etc.)
    """
    prompt_text = prompt_text.lower()
    input_fields_lower = [field.lower() for field in input_fields]
    output_fields_lower = [field.lower() for field in output_fields]
    
    # Check for classification tasks
    if any(term in prompt_text for term in ["classify", "categorize", "label", "sentiment"]) or \
       any(field in output_fields_lower for field in ["class", "category", "label", "sentiment"]):
        return "classification"
    
    # Check for extraction tasks
    if any(term in prompt_text for term in ["extract", "identify", "find", "locate"]) or \
       "entities" in output_fields_lower or "extracted" in output_fields_lower:
        return "extraction"
    
    # Check for summarization tasks
    if any(term in prompt_text for term in ["summarize", "summary", "condense", "shorten"]) or \
       any(field in output_fields_lower for field in ["summary", "abstract"]):
        return "summarization"
    
    # Check for generation tasks
    if any(term in prompt_text for term in ["generate", "create", "write", "compose"]) or \
       any(field in output_fields_lower for field in ["text", "content", "response", "answer"]):
        return "generation"
    
    # Check for reasoning tasks
    if any(term in prompt_text for term in ["reason", "think", "analyze", "evaluate", "solve"]) or \
       any(field in output_fields_lower for field in ["reasoning", "analysis", "solution"]):
        return "reasoning"
    
    # Check for coding tasks
    if any(term in prompt_text for term in ["code", "program", "function", "implement"]) or \
       any(field in output_fields_lower for field in ["code", "implementation", "function"]):
        return "coding"
    
    # Default to general task type
    return "general"


def select_instruction_preference(task_type: str, prompt_data: Dict[str, Any]) -> List[str]:
    """
    Select appropriate instruction preferences based on the task type.
    
    Args:
        task_type: The type of task (e.g., "classification", "generation")
        prompt_data: Dictionary containing prompt data
        
    Returns:
        List of selected instruction preferences or empty list if not available
    """
    # Get Llama-specific tips
    instruction_preferences = LLAMA_TIPS.get("instruction_preferences", [])
    
    if not instruction_preferences:
        return []
    
    # Task-specific preference indices
    task_preference_map = {
        "classification": [2, 7, 8],  # Reasoning, chain-of-thought, validation
        "extraction": [0, 3, 12],   # OBSERVE-DECIDE-EXECUTE, sectioned response, problem-solving
        "summarization": [3, 7, 14],  # Sectioned response, chain-of-thought, documentation
        "generation": [5, 10, 11],  # Formatting, code generation, role-based
        "reasoning": [2, 7, 12, 15],   # Reasoning steps, chain-of-thought, problem-solving
        "coding": [1, 4, 10],      # Function structure, error checking, code generation
        "general": [0, 3, 7]       # OBSERVE-DECIDE-EXECUTE, sectioned response, chain-of-thought
    }
    
    # Get indices for the current task type
    indices = task_preference_map.get(task_type, task_preference_map["general"])
    
    # Select preferences based on indices
    selected_preferences = [instruction_preferences[i] for i in indices if i < len(instruction_preferences)]
    
    # Add a random preference for variety if we have fewer than 3
    if len(selected_preferences) < 3 and len(instruction_preferences) > 3:
        remaining = [p for i, p in enumerate(instruction_preferences) if i not in indices]
        if remaining:
            selected_preferences.append(random.choice(remaining))
    
    return selected_preferences


def format_prompt_for_llama(instruction: str, context: str = "", examples: List[Dict[str, Any]] = None) -> str:
    """
    Format a prompt for Llama models using the appropriate template.
    
    Args:
        instruction: The main instruction text
        context: Optional context information
        examples: Optional list of examples
        
    Returns:
        Formatted prompt string
    """
    if examples is None:
        examples = []
    
    # Determine which template to use based on what's provided
    if context and examples:
        template_type = "full"
    elif context:
        template_type = "with_context"
    elif examples:
        template_type = "with_examples"
    else:
        template_type = "basic"
    
    # Get the template
    template = get_llama_template(template_type)
    
    # Format examples if provided
    formatted_examples = ""
    if examples:
        for i, example in enumerate(examples):
            formatted_examples += f"Example {i+1}:\n"
            for key, value in example.items():
                formatted_examples += f"{key}: {value}\n"
            formatted_examples += "\n"
    
    # Apply the template
    return template.format(
        instruction=instruction,
        context=context,
        examples=formatted_examples
    )
