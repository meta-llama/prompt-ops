# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Prompt processing chain of responsibility implementation.

This module contains the base PromptProcessor class and specific processors
that can be chained together to process prompts in a flexible, composable way.
"""

from typing import Dict, Any, Optional, List

from .utils.llama_utils import (
    get_task_type_from_prompt,
    select_instruction_preference,
    format_prompt_for_llama
)


class PromptProcessor:
    """
    Base class for prompt processors in a chain of responsibility pattern.
    
    Each processor can modify the prompt data and then pass it to the next
    processor in the chain.
    """
    
    def __init__(self, next_processor: Optional["PromptProcessor"] = None):
        """
        Initialize a prompt processor.
        
        Args:
            next_processor: The next processor in the chain
        """
        self.next = next_processor
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the prompt data and pass it to the next processor.
        
        Args:
            data: The prompt data to process
            
        Returns:
            The processed prompt data
        """
        # Base implementation just passes to the next processor
        if self.next:
            return self.next.process(data)
        return data
    
    def set_next(self, processor: "PromptProcessor") -> "PromptProcessor":
        """
        Set the next processor in the chain.
        
        Args:
            processor: The next processor
            
        Returns:
            The next processor for method chaining
        """
        self.next = processor
        return processor


class LlamaFormatting(PromptProcessor):
    """
    Processor that applies Llama-specific formatting to prompts.
    """
    
    def __init__(self, next_processor: Optional[PromptProcessor] = None, apply_templates: bool = True):
        """
        Initialize the Llama formatting processor.
        
        Args:
            next_processor: The next processor in the chain
            apply_templates: Whether to apply Llama-specific templates
        """
        super().__init__(next_processor)
        self.apply_templates = apply_templates
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply Llama-specific formatting to the prompt.
        
        Args:
            data: The prompt data to process
            
        Returns:
            The processed prompt data
        """
        # Skip processing if formatting is disabled
        if not data.get("apply_formatting", True):
            return super().process(data)
        
        # Extract examples from prompt_data if available
        examples = data.get("examples", [])
        context = data.get("context", "")
        instruction = data.get("text", "")
        
        # Apply Llama-specific template formatting if enabled
        if self.apply_templates:
            formatted_prompt = format_prompt_for_llama(
                instruction=instruction,
                context=context,
                examples=examples
            )
            data["text"] = formatted_prompt
        
        # Pass to the next processor
        return super().process(data)


class InstructionPreference(PromptProcessor):
    """
    Processor that adds task-specific instruction preferences to prompts.
    """
    
    def __init__(self, next_processor: Optional[PromptProcessor] = None, verbose: bool = False):
        """
        Initialize the instruction preference processor.
        
        Args:
            next_processor: The next processor in the chain
            verbose: Whether to print verbose output
        """
        super().__init__(next_processor)
        self.verbose = verbose
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add task-specific instruction preferences to the prompt.
        
        Args:
            data: The prompt data to process
            
        Returns:
            The processed prompt data
        """
        # Extract input and output fields from the prompt data
        input_fields = data.get("input_fields", [])
        output_fields = data.get("output_fields", [])
        prompt_text = data.get("text", "")
        
        task_type = get_task_type_from_prompt(prompt_text, input_fields, output_fields)
        
        # Select appropriate instruction preferences based on the task type
        selected_preferences = select_instruction_preference(task_type, data)
        
        data["_selected_preferences"] = selected_preferences
        
        if selected_preferences:
            # Add the preferences as meta-instructions for MIPROv2's proposer
            proposer_kwargs = data.get("proposer_kwargs", {}) or {}
            
            # Combine all preferences into a single tip string
            combined_tip = "\n".join([f"{i+1}. {pref}" for i, pref in enumerate(selected_preferences)])
            instruction_tip = f"Apply the following instruction formats to optimize the prompt:\n{combined_tip}"
            
            # Store in proposer_kwargs for the MIPROv2 proposer
            proposer_kwargs['tip'] = instruction_tip
            data["proposer_kwargs"] = proposer_kwargs
            
            # Also store the tip directly in the strategy for YAML export
            data["instruction_tips"] = instruction_tip
            
            # Log the task type and selected preferences if verbose
            if self.verbose:
                print(f"Task type detected: {task_type}")
                for i, pref in enumerate(selected_preferences):
                    print(f"Selected instruction preference {i+1}: {pref[:50]}...")
        
        # Pass to the next processor
        return super().process(data)


def create_llama_processing_chain(apply_formatting: bool = True, 
                                 apply_templates: bool = True,
                                 verbose: bool = False) -> PromptProcessor:
    """
    Create a processing chain for Llama-specific prompt optimization.
    
    Args:
        apply_formatting: Whether to apply Llama-specific formatting
        apply_templates: Whether to apply Llama-specific templates
        verbose: Whether to print verbose output
        
    Returns:
        The first processor in the chain
    """
    # Create processors
    instruction_processor = InstructionPreference(verbose=verbose)
    formatting_processor = LlamaFormatting(instruction_processor, apply_templates=apply_templates)
    
    # Return the first processor in the chain
    return formatting_processor
