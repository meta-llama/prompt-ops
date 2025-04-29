# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
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
from .prompt_processors import PromptProcessor, create_llama_processing_chain
from .utils.llama_utils import is_llama_model

class LlamaStrategy(BaseStrategy):
    """
    Optimization strategy specifically tailored for Llama models.
    
    This strategy uses composition with the Chain of Responsibility pattern to process prompts
    with Llama-specific formatting and optimization techniques before passing
    them to a BasicOptimizationStrategy for optimization.
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
        
        # Create the base optimization strategy
        self.base_strategy = BasicOptimizationStrategy(
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
        self.verbose = kwargs.get('verbose', False)
        
        # Create the processing chain
        self.processor_chain = create_llama_processing_chain(
            apply_formatting=apply_formatting,
            apply_templates=apply_templates,
            verbose=self.verbose
        )
        
        # Forward essential attributes from base_strategy for compatibility
        self.task_model = getattr(self.base_strategy, 'task_model', None)
        self.prompt_model = getattr(self.base_strategy, 'prompt_model', None)
        self.trainset = getattr(self.base_strategy, 'trainset', None)
        self.valset = getattr(self.base_strategy, 'valset', None)
        
    def run(self, prompt_data: Dict[str, Any]) -> Any:
        """Apply Llama-specific optimization to the prompt.
        
        Uses a chain of processors to apply Llama-specific formatting and
        instruction preferences before passing to the optimizer.
        
        Args:
            prompt_data: Dictionary containing the prompt text and metadata
            
        Returns:
            The optimized DSPy program object
        """
        # Add strategy parameters to prompt data for processors
        prompt_data_copy = prompt_data.copy()
        prompt_data_copy["apply_formatting"] = self.apply_formatting
        prompt_data_copy["apply_templates"] = self.apply_templates
        
        # Process the prompt data through the chain
        processed_data = self.processor_chain.process(prompt_data_copy)
        
        # Extract any proposer kwargs that were added by processors
        if "proposer_kwargs" in processed_data:
            # Ensure the base strategy has proposer_kwargs
            if not hasattr(self.base_strategy, 'proposer_kwargs') or not self.base_strategy.proposer_kwargs:
                self.base_strategy.proposer_kwargs = {}
                
            # Transfer proposer kwargs to the base strategy
            self.base_strategy.proposer_kwargs.update(processed_data["proposer_kwargs"])
            
            # If we have a tip, store it for YAML export
            if 'tip' in processed_data["proposer_kwargs"]:
                self.tip = processed_data["proposer_kwargs"]['tip']
            
        # Store selected preferences for reference if available
        if "_selected_preferences" in processed_data:
            self._selected_preferences = processed_data["_selected_preferences"]
            
        # Store instruction tips for YAML export if available
        if "instruction_tips" in processed_data:
            self.instruction_tips = processed_data["instruction_tips"]
        
        # Ensure the base strategy has the latest models and datasets
        # This is important because these might be set after initialization
        self.base_strategy.task_model = self.task_model
        self.base_strategy.prompt_model = self.prompt_model
        self.base_strategy.trainset = self.trainset
        self.base_strategy.valset = self.valset
        
        # Delegate to the base strategy for optimization
        return self.base_strategy.run(processed_data)


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


# Add methods to LlamaStrategy to handle attribute setting
def __setattr__(self, name, value):
    """
    Override attribute setting to forward important attributes to the base strategy.
    """
    # Set the attribute on self first
    object.__setattr__(self, name, value)
    
    # Forward specific attributes to the base strategy if it exists
    if hasattr(self, 'base_strategy') and name in [
        'task_model', 'prompt_model', 'trainset', 'valset', 'metric'
    ]:
        setattr(self.base_strategy, name, value)

# Add the __setattr__ method to LlamaStrategy
LlamaStrategy.__setattr__ = __setattr__
