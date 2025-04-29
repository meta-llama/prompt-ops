# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Utility functions for formatting and converting between different file formats.
"""

import json


def convert_json_to_yaml(prompt, few_shots, user_prompt=None, task_model=None, model_family=None, strategy=None):
    """
    Convert prompt data from JSON format to YAML format.
    
    Args:
        prompt: The system prompt text
        few_shots: List of few-shot examples
        user_prompt: Optional user prompt to append to the YAML file
        task_model: Optional task model information
        model_family: Optional model family information
        strategy: Optional optimization strategy object
        
    Returns:
        str: The formatted YAML content
    """
    # Format the prompt text with proper indentation
    indented_prompt = "\n    ".join(prompt.strip().split("\n"))
    
    # Start building the YAML content with the prompt
    yaml_content = f"""system: |-
            {indented_prompt}

        Few-shot examples:
            """
            
    # Add each few_shot example
    for i, example in enumerate(few_shots, 1):
        question = example.get("question", "")
        answer = example.get("answer", "")
        context = example.get("context", "")
        
        # Format the question with proper indentation
        indented_question = "\n        ".join(question.strip().split("\n"))
        
        # Format the answer with proper indentation
        indented_answer = "\n        ".join(answer.strip().split("\n"))
        
        # Format the context with proper indentation
        if context:
            # Handle case where context might be a list
            if isinstance(context, list):
                # Convert list to string representation
                context_str = str(context)
                indented_context = "\n        ".join(context_str.strip().split("\n"))
            else:
                # Handle string context as before
                indented_context = "\n        ".join(context.strip().split("\n"))
            
            # Add the example to the YAML content
            yaml_content += f"""
                Q:<!> {indented_question} <!>
                C:<#> {indented_context} <#>
                A: {indented_answer}
            """ 
        else:
            # Add the example to the YAML content without context
            yaml_content += f"""
                Example {i}:
                    Question: {indented_question}
                    Answer: {indented_answer}
            """
    
    # Add user prompt if provided
    if user_prompt:
        indented_user_prompt = "\n    ".join(user_prompt.strip().split("\n"))
        yaml_content += f"\n\nuser: |-\n    {indented_user_prompt}"
        
    # Add config section with task model and optimization info if available
    if task_model:
        model_name = getattr(task_model, 'model_name', str(task_model))
        yaml_content += "\n\nconfig:\n"
        yaml_content += f"  task_model: {model_name}\n"
        
        # Add model family info if available
        if model_family:
            yaml_content += f"  model_family: {model_family}\n"
        
        # Add detailed strategy info if available
        if strategy:
            strategy_name = strategy.__class__.__name__
            yaml_content += f"  optimization:\n"
            yaml_content += f"    name: {strategy_name}\n"
            
            # Add strategy-specific parameters if available
            if hasattr(strategy, 'model_name'):
                yaml_content += f"    model_name: {strategy.model_name}\n"
            
            # Include model-specific settings for LlamaStrategy
            if strategy_name == "LlamaStrategy":
                if hasattr(strategy, 'apply_formatting'):
                    yaml_content += f"    apply_formatting: {strategy.apply_formatting}\n"
                
                if hasattr(strategy, 'apply_templates'):
                    yaml_content += f"    apply_templates: {strategy.apply_templates}\n"
            
            # Extract and include instruction tips if available
            if hasattr(strategy, 'instruction_tips'):
                # Use the directly stored instruction_tips attribute
                tip = strategy.instruction_tips
                # Format the tip with proper indentation for YAML
                indented_tip = "\n        ".join(tip.strip().split("\n"))
                yaml_content += f"    instruction_tips: |\n        {indented_tip}\n"
            # Fall back to proposer_kwargs if instruction_tips not available
            elif hasattr(strategy, 'proposer_kwargs') and strategy.proposer_kwargs and 'tip' in strategy.proposer_kwargs:
                tip = strategy.proposer_kwargs['tip']
                # Format the tip with proper indentation for YAML
                indented_tip = "\n        ".join(tip.strip().split("\n"))
                yaml_content += f"    instruction_tips: |\n        {indented_tip}\n"
            
            # For LlamaStrategy, include original instruction preferences if available
            if strategy_name == "LlamaStrategy" and hasattr(strategy, '_selected_preferences'):
                yaml_content += f"    original_preferences:\n"
                for i, pref in enumerate(strategy._selected_preferences):
                    indented_pref = "\n        ".join(pref.strip().split("\n"))
                    yaml_content += f"      - |\n        {indented_pref}\n"
    
    return yaml_content


def json_to_yaml_file(input_file, output_file, user_prompt=None, task_model=None, model_family=None, strategy=None):
    """
    Convert a JSON prompt file to YAML format and save it.
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output YAML file
        user_prompt: Optional user prompt to append to the YAML file
        task_model: Optional task model information
        model_family: Optional model family information
        strategy: Optional optimization strategy object
    """
    # Read the JSON file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Extract the prompt and few_shots from the JSON
    prompt = data.get("prompt", "")
    few_shots = data.get("few_shots", [])
    
    # Convert to YAML
    yaml_content = convert_json_to_yaml(
        prompt, 
        few_shots, 
        user_prompt=user_prompt,
        task_model=task_model,
        model_family=model_family,
        strategy=strategy
    )
    
    # Write the YAML file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)
