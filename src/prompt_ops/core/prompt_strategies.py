"""
Strategy implementations for prompt optimization.

This module contains the base strategy class and various specialized
optimization strategies for migrating prompts to Llama models.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable
import dspy
from typing_extensions import Literal

from .utils import map_auto_mode_to_dspy

class OptimizationError(Exception):
    """Exception raised when prompt optimization fails."""
    pass

class BaseStrategy(ABC):
    """
    Base class for prompt optimization strategies.
    
    This class defines the interface for optimization strategies and provides
    common functionality.
    """
    
    def __init__(
        self, 
        model_name: str = "llama-3",
        metric: Optional[Callable] = None,
        num_threads: int = 36,
        model_family: str = None
    ):
        """
        Initialize the strategy.
        
        Args:
            model_name: Name of the model to optimize for
            metric: Metric to use for evaluation
            num_threads: Number of threads to use for parallel processing
            model_family: Model family to optimize for (e.g., "llama", "gpt", "claude")
                         If None, will be inferred from model_name
        """
        self.model_name = model_name
        self.metric = metric
        self.num_threads = num_threads
        self.trainset = None
        self.valset = None
        

        if model_family is None:
            from .utils.llama_utils import is_llama_model
            if is_llama_model(model_name):
                self.model_family = "llama"
            else:
                # Default to Llama since that's our focus
                logging.warning(f"Model '{model_name}' does not appear to be a Llama model. "
                              f"This library is optimized for Llama models.")
                self.model_family = "llama"
        else:
            # If model_family is explicitly provided, use it but warn if not 'llama'
            self.model_family = model_family
            if self.model_family != "llama":
                logging.warning(f"Model family '{self.model_family}' specified, but this library "
                              f"is optimized for Llama models.")
    
    @abstractmethod
    def run(self, prompt_data: Dict[str, Any]) -> Any:
        """
        Execute the optimization strategy on the given prompt data.
        
        Args:
            prompt_data: Dictionary containing prompt information
                - text: The prompt text to optimize
                - inputs: List of input field names
                - outputs: List of output field names
                
        Returns:
            The optimized prompt text
        """
        text = prompt_data.get("text", "")
        # Default behavior: no changes
        return text


class BasicOptimizationStrategy(BaseStrategy):
    """
    A strategy that runs a basic optimization pass using DSPy's MIPROv2.
    
    This strategy applies a basic optimization to the prompt using DSPy's
    MIPROv2 optimizer with the 'basic' auto mode, which focuses on format
    and style adjustments without extensive restructuring.
    
    This strategy can be model-aware, incorporating model-specific tips and
    formatting preferences into the optimization process.
    """
    
    def __init__(
        self, 
        model_name: str = "llama-3", 
        num_threads: int = 36,
        metric: Optional[Callable] = None,
        model_family: str = None,
        # MIPROv2 specific parameters
        max_bootstrapped_demos: int = 4,
        max_labeled_demos: int = 5,
        auto: Optional[Literal["basic", "intermediate", "advanced"]] = "basic",
        num_candidates: int = 10,
        max_errors: int = 10,
        seed: int = 9,
        init_temperature: float = 0.5,
        verbose: bool = False,
        track_stats: bool = True,
        log_dir: Optional[str] = None,
        metric_threshold: Optional[float] = None,
        # Compile method parameters
        num_trials: Optional[int] = None,
        minibatch: bool = True,
        minibatch_size: int = 25,
        minibatch_full_eval_steps: int = 10,
        program_aware_proposer: bool = True,
        data_aware_proposer: bool = True,
        view_data_batch_size: int = 10,
        tip_aware_proposer: bool = True,
        fewshot_aware_proposer: bool = True,
        use_llama_tips: bool = True,
        requires_permission_to_run: bool = False,
        **kwargs
    ):
        """
        Initialize the basic optimization strategy with MIPROv2 parameters.
        
        Args:
            model_name: Target Llama model name
            num_threads: Number of threads for optimization
            metric: Evaluation metric function
            
            # MIPROv2 constructor parameters
            max_bootstrapped_demos: Maximum number of bootstrapped demos to generate
            max_labeled_demos: Maximum number of labeled demos to include
            auto: Optimization mode ('basic', 'intermediate', 'advanced')
                 These values are mapped to DSPy's expected values ('light', 'medium', 'heavy')
            num_candidates: Number of candidate instructions to generate
            max_errors: Maximum number of errors to tolerate during evaluation
            seed: Random seed for reproducibility
            init_temperature: Initial temperature for sampling
            verbose: Whether to print verbose output
            track_stats: Whether to track statistics
            log_dir: Directory to save logs
            metric_threshold: Threshold for early stopping based on metric
            
            # MIPROv2 compile method parameters
            num_trials: Number of optimization trials (if None, determined by auto mode)
            minibatch: Whether to use minibatching for evaluation
            minibatch_size: Size of minibatches for evaluation
            minibatch_full_eval_steps: How often to evaluate on the full validation set
            program_aware_proposer: Whether to use program-aware instruction proposals
            data_aware_proposer: Whether to use data-aware instruction proposals
            view_data_batch_size: Number of examples to show to the proposer
            tip_aware_proposer: Whether to use tip-aware instruction proposals
            fewshot_aware_proposer: Whether to use few-shot aware instruction proposals
            requires_permission_to_run: Whether to require user permission to run
            provide_traceback: Whether to provide tracebacks for errors
            
            **kwargs: Additional configuration parameters
        """
        super().__init__(model_name, metric, num_threads, model_family)
        
        # Store task and prompt models
        self.task_model = kwargs.get('task_model')
        self.prompt_model = kwargs.get('prompt_model')
        
        # Training and validation data
        self.trainset = kwargs.get('trainset', [])
        self.valset = kwargs.get('valset', [])
        
        # Model-specific optimization settings
        self.use_llama_tips = use_llama_tips
        
        # MIPROv2 constructor parameters
        self.max_bootstrapped_demos = max_bootstrapped_demos
        self.max_labeled_demos = max_labeled_demos
        self.auto = auto
        self.num_candidates = num_candidates
        self.max_errors = max_errors
        self.seed = seed
        self.init_temperature = init_temperature
        self.verbose = verbose
        self.track_stats = track_stats
        self.log_dir = log_dir
        self.metric_threshold = metric_threshold
        
        # MIPROv2 compile method parameters
        self.num_trials = num_trials
        self.minibatch = minibatch
        self.minibatch_size = minibatch_size
        self.minibatch_full_eval_steps = minibatch_full_eval_steps
        self.program_aware_proposer = program_aware_proposer
        self.data_aware_proposer = data_aware_proposer
        self.view_data_batch_size = view_data_batch_size
        self.tip_aware_proposer = tip_aware_proposer
        self.fewshot_aware_proposer = fewshot_aware_proposer
        self.requires_permission_to_run = requires_permission_to_run
        

    
    def run(self, prompt_data: Dict[str, Any]) -> Any:
        """
        Apply basic optimization to the prompt using DSPy's MIPROv2.
        
        Args:
            prompt_data: Dictionary containing the prompt text and metadata
        
        Returns:
            The optimized DSPy program object, which contains the optimized prompt
            accessible via optimized_program.predict.signature.instructions
        """
        text = prompt_data["text"]
        
        if 'dspy' not in globals() or not self.trainset:
            return f"[Optimized for {self.model_name}] {text}"
        
        try:
            # Add model-specific tips to the prompt if enabled
            model_tips = None
            if self.use_llama_tips:
                # Check if model_tips are already in prompt_data
                if "model_tips" in prompt_data:
                    model_tips = prompt_data["model_tips"]
                else:
                    # Import here to avoid circular imports
                    from .utils.llama_utils import get_llama_tips
                    model_tips = get_llama_tips()
                    
            # Incorporate model-specific tips into the prompt if available
            if model_tips and isinstance(model_tips, dict):
                # Add model-specific formatting tips to the prompt
                if "formatting" in model_tips:
                    text += f"\n\nFormatting Tip: {model_tips['formatting']}"
                
                # Add reasoning tips for complex tasks
                if "reasoning" in model_tips and any(field in prompt_data.get('inputs', []) for field in ["context", "document", "text"]):
                    text += f"\n\nReasoning Tip: {model_tips['reasoning']}"
                
                # Add constraint tips if output format is important
                if "constraints" in model_tips:
                    text += f"\n\nOutput Requirements: {model_tips['constraints']}"
                    
            # Update the prompt text in prompt_data
            prompt_data["text"] = text
            # Create a signature class dynamically with proper field definitions
            input_fields = {}
            output_fields = {}
            
            # Define input and output fields based on prompt_data
            for field in prompt_data.get('inputs', ['question']):
                input_fields[field] = dspy.InputField(desc="${" + field + "}")
            for field in prompt_data.get('outputs', ['answer']):
                output_fields[field] = dspy.OutputField(desc="${" + field + "}")
                
            # Create the signature class with proper field definitions
            DynamicSignature = type('DynamicSignature', (dspy.Signature,), {
                **input_fields,
                **output_fields,
                '__doc__': text  # Store the instructions as the docstring
            })
            
            # Create program instance with the signature
            program = dspy.Predict(DynamicSignature)
            
            # Map our naming convention to DSPy's expected values
            dspy_auto_mode = map_auto_mode_to_dspy(self.auto)
            
            # Extract the underlying DSPy model if we have model adapters
            task_model = self.task_model
            prompt_model = self.prompt_model
            
            # Handle DSPyModelAdapter instances
            if hasattr(task_model, '_model'):
                task_model = task_model._model
                
            if hasattr(prompt_model, '_model'):
                prompt_model = prompt_model._model
                
            # Configure the optimizer with all parameters
            optimizer = dspy.MIPROv2(
                metric=self.metric,
                prompt_model=prompt_model,
                task_model=task_model,
                max_bootstrapped_demos=self.max_bootstrapped_demos,
                max_labeled_demos=self.max_labeled_demos,
                auto=dspy_auto_mode,  # Use the mapped value
                num_candidates=self.num_candidates,
                num_threads=self.num_threads,
                max_errors=self.max_errors,
                seed=self.seed,
                init_temperature=self.init_temperature,
                verbose=self.verbose,
                track_stats=self.track_stats,
                log_dir=self.log_dir,
                metric_threshold=self.metric_threshold
            )
            
            # If we have model-specific tips, configure the proposer to use them
            if model_tips and hasattr(optimizer, 'proposer_kwargs'):
                optimizer.proposer_kwargs = getattr(optimizer, 'proposer_kwargs', {}) or {}
                # Add persona and example tips to the proposer
                if 'persona' in model_tips or 'examples' in model_tips:
                    persona_tip = model_tips.get('persona', '')
                    examples_tip = model_tips.get('examples', '')
                    optimizer.proposer_kwargs['tip'] = f"{persona_tip} {examples_tip}".strip()
            
            logging.info(f"Optimization strategy using {self.max_labeled_demos} labeled demos, {self.max_bootstrapped_demos} bootstrapped demos with {self.num_threads} threads")
            
            logging.info(f"Compiling program with {len(self.trainset)} training examples and {len(self.valset)} validation examples")
            
            # Call compile with all parameters
            optimized_program = optimizer.compile(
                program,
                trainset=self.trainset,
                valset=self.valset,
                num_trials=self.num_trials,
                minibatch=self.minibatch,
                minibatch_size=self.minibatch_size,
                minibatch_full_eval_steps=self.minibatch_full_eval_steps,
                program_aware_proposer=self.program_aware_proposer,
                data_aware_proposer=self.data_aware_proposer,
                view_data_batch_size=self.view_data_batch_size,
                tip_aware_proposer=self.tip_aware_proposer,
                fewshot_aware_proposer=self.fewshot_aware_proposer,
                requires_permission_to_run=self.requires_permission_to_run
            )
            
            # Store model family information in the optimized program for reference
            if hasattr(self, 'model_family') and optimized_program is not None:
                setattr(optimized_program, 'model_family', self.model_family)
            
            # Check if optimization was successful
            if optimized_program is None:
                raise OptimizationError("Optimizer returned None. This could be due to insufficient examples or model errors.")
            
            # Log information about the optimized program
            logging.info(f"Optimized program type: {type(optimized_program)}")
            logging.info(f"Optimized program attributes: {dir(optimized_program)}")
            
            return optimized_program
            
        except Exception as e:
            logging.error(f"Error in optimization: {str(e)}")
            # Instead of creating a mock program, raise a more descriptive exception
            raise OptimizationError(f"Optimization failed: {str(e)}")
