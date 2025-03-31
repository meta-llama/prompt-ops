"""
Llama-specific optimization strategies.

This module contains optimization strategies that are tailored for Llama models,
building on the base strategies in prompt_strategies.py.
"""

import logging
import warnings
from typing import Dict, Any, List, Optional, Callable, Literal, Union

import dspy

from .prompt_strategies import BaseStrategy, BasicOptimizationStrategy, OptimizationError
from .utils.llama_utils import (
    is_llama_model, get_llama_tips, get_llama_template, 
    get_task_type_from_prompt, select_instruction_preference,
    format_prompt_for_llama
)

class LlamaStrategy(BasicOptimizationStrategy):
    """
    Optimization strategy specifically tailored for Llama models.
    
    This strategy extends the BasicOptimizationStrategy with additional
    Llama-specific formatting and optimization techniques.
    """
    
    def __init__(
        self, 
        model_name: str = "llama-3", 
        num_threads: int = 36,
        metric: Optional[Callable] = None,
        apply_formatting: bool = True,
        apply_templates: bool = True,
        template_type: str = "basic",
        max_bootstrapped_demos: int = 4,
        max_labeled_demos: int = 5,
        auto: Optional[Literal["basic", "intermediate", "advanced"]] = "basic",
        **kwargs
    ):
        """
        Initialize the Llama-specific strategy.
        
        Args:
            model_name: Name of the Llama model to optimize for
            num_threads: Number of threads to use for parallel processing
            metric: Metric to use for evaluation
            apply_formatting: Whether to apply Llama-specific formatting
            apply_templates: Whether to apply Llama-specific templates
            template_type: Type of template to use (basic, with_context, with_examples, full)
            max_bootstrapped_demos: Maximum number of bootstrapped demos for MIPROv2
            max_labeled_demos: Maximum number of labeled demos for MIPROv2
            auto: Auto mode for MIPROv2 (basic, intermediate, advanced)
            **kwargs: Additional parameters for BasicOptimizationStrategy
        """
        # Verify that the model is a Llama model
        if not is_llama_model(model_name):
            warnings.warn(f"Model '{model_name}' does not appear to be a Llama model. "
                         f"This strategy is optimized for Llama models and may not work as expected.")
        
        super().__init__(
            model_name=model_name,
            num_threads=num_threads,
            metric=metric,
            max_bootstrapped_demos=max_bootstrapped_demos,
            max_labeled_demos=max_labeled_demos,
            auto=auto,
            **kwargs
        )
        
        # Store Llama-specific parameters
        self.apply_formatting = apply_formatting
        self.apply_templates = apply_templates
        self.template_type = template_type
        
    def run(self, prompt_data: Dict[str, Any]) -> Any:
        """Apply Llama-specific optimization to the prompt.
        
        Incorporates Llama-specific instruction preferences and formatting based on task type.
        
        Args:
            prompt_data: Dictionary containing the prompt text and metadata
            
        Returns:
            The optimized DSPy program object
        """
        # Apply Llama-specific formatting if enabled
        if self.apply_formatting:
            # Extract examples from prompt_data if available
            examples = prompt_data.get("examples", [])
            context = prompt_data.get("context", "")
            instruction = prompt_data.get("text", "")
            
            # Apply Llama-specific template formatting if enabled
            if self.apply_templates:
                formatted_prompt = format_prompt_for_llama(
                    instruction=instruction,
                    context=context,
                    examples=examples
                )
                prompt_data["text"] = formatted_prompt
        
        # Extract input and output fields from the prompt data
        input_fields = prompt_data.get("input_fields", [])
        output_fields = prompt_data.get("output_fields", [])
        prompt_text = prompt_data.get("text", "")
        
        # Determine the task type
        task_type = get_task_type_from_prompt(prompt_text, input_fields, output_fields)
        
        # Select appropriate instruction preferences based on the task type
        selected_preferences = select_instruction_preference(task_type, prompt_data)
        
        # Store the original selected preferences for later reference
        self._selected_preferences = selected_preferences
        
        if selected_preferences:
            # Add the selected instruction preferences to the prompt
            text = prompt_data.get("text", "")
            text += "\n\nFollow these instruction formats:\n"
            for i, preference in enumerate(selected_preferences):
                text += f"{i+1}. {preference}\n"
            prompt_data["text"] = text
            
            # Combine all instruction preferences into a single tip string for MIPROv2
            self.proposer_kwargs = getattr(self, 'proposer_kwargs', {}) or {}
            if selected_preferences:
                # Combine all preferences into a single tip string
                combined_tip = "\n".join([f"{i+1}. {pref}" for i, pref in enumerate(selected_preferences)])
                self.proposer_kwargs['tip'] = f"Apply the following instruction formats to optimize the prompt:\n{combined_tip}"
            
            # Log the task type and selected preferences if verbose
            if getattr(self, 'verbose', False):
                print(f"Task type detected: {task_type}")
                for i, pref in enumerate(selected_preferences):
                    print(f"Selected instruction preference {i+1}: {pref[:50]}...")
        
        # Call the parent class's run method to apply optimization
        return super().run(prompt_data)


def get_strategy_for_model(model_name: str, **kwargs) -> BaseStrategy:
    """
    Factory function to create a Llama strategy for a given model.
    
    Args:
        model_name: Name of the model to optimize for
        **kwargs: Additional parameters for the strategy
    
    Returns:
        A LlamaStrategy instance
    """
    if not is_llama_model(model_name):
        warnings.warn(f"Model '{model_name}' does not appear to be a Llama model. "
                     f"This library is optimized for Llama models and may not work as expected with other models.")
    
    return LlamaStrategy(model_name=model_name, **kwargs)
